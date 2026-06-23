from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.db.models.worker import Worker, PlatformEnum, OnboardingStatusEnum
from app.db.models.session import Session
from app.whatsapp.client import send_text_message, send_interactive_buttons
from app.onboarding.platform_validation import validate_partner_id
from app.onboarding.otp_service import generate_otp, store_otp, verify_otp
from app.onboarding.policy_service import create_policy_for_worker
from datetime import datetime, timezone
from app.whatsapp.session_manager import (
    get_active_session,
    get_worker_by_whatsapp_id,
    create_session,
)
from app.whatsapp.message_parser import ParsedMessage
import logging

logger = logging.getLogger(__name__)


async def handle_onboarding(parsed: ParsedMessage, db: AsyncSession) -> dict:
    """Route incoming message to the correct onboarding step."""
    whatsapp_id = parsed.whatsapp_id
    worker = await get_worker_by_whatsapp_id(whatsapp_id, db)

    # --- Step 1: New worker — send welcome + platform selection ---
    if not worker:
        await _step1_welcome(whatsapp_id)
        new_worker = Worker(
            whatsapp_id=whatsapp_id,
            partner_id=f"PENDING_{whatsapp_id}",
            platform=PlatformEnum.zepto,
            full_name="Pending",
            phone_number=whatsapp_id,
            zone="Pending",
            tier="standard",
            preferred_language="en",
            onboarding_status=OnboardingStatusEnum.pending_platform,
            # created_at / updated_at handled by model defaults
        )
        db.add(new_worker)
        await db.commit()
        await db.refresh(new_worker)
        await create_session(new_worker.id, whatsapp_id, db)
        return {"step": "started"}

    status = worker.onboarding_status

    if status == OnboardingStatusEnum.pending_platform:
        return await _step2_platform_selected(parsed, worker, db)

    if status == OnboardingStatusEnum.pending_partner_id:
        return await _step3_validate_partner_id(parsed, worker, db)

    if status == OnboardingStatusEnum.pending_otp:
        return await _step4_verify_otp(parsed, worker, db)

    return {"step": "unknown"}


async def _step1_welcome(whatsapp_id: str):
    await send_interactive_buttons(
        to=whatsapp_id,
        body=(
            "👋 Welcome to *GigInsurance*!\n\n"
            "Income protection for delivery partners.\n\n"
            "Which platform do you deliver for?"
        ),
        buttons=[
            {"id": "platform_zepto", "title": "⚡ Zepto"},
            {"id": "platform_blinkit", "title": "🟡 Blinkit"},
        ],
    )


async def _step2_platform_selected(
    parsed: ParsedMessage, worker: Worker, db: AsyncSession
) -> dict:
    button_id = parsed.button_id
    text = (parsed.text or "").strip()

    # Resolve platform from button (Meta) OR number reply (Twilio degraded)
    platform = None
    if button_id and button_id.startswith("platform_"):
        platform = button_id.replace("platform_", "")
    elif text == "1":
        platform = "zepto"
    elif text == "2":
        platform = "blinkit"

    if not platform:
        await send_text_message(
            worker.whatsapp_id,
            "Please reply *1* for Zepto or *2* for Blinkit.",
        )
        return {"step": "waiting_platform"}

    await db.execute(
        update(Worker)
        .where(Worker.id == worker.id)
        .values(
            platform=PlatformEnum(platform),
            onboarding_status=OnboardingStatusEnum.pending_partner_id,
        )
    )
    await db.commit()

    await send_text_message(
        worker.whatsapp_id,
        f"Got it! You're on *{platform.capitalize()}*. ✅\n\n"
        f"Please send your *Partner ID* (e.g. ZPT001 or BLK001).",
    )
    return {"step": "platform_selected"}


async def _step3_validate_partner_id(
    parsed: ParsedMessage, worker: Worker, db: AsyncSession
) -> dict:
    partner_id = parsed.text
    if not partner_id:
        await send_text_message(
            worker.whatsapp_id,
            "Please type your Partner ID (e.g. ZPT001).",
        )
        return {"step": "waiting_partner_id"}

    platform_data = validate_partner_id(worker.platform.value, partner_id)
    if not platform_data:
        await send_text_message(
            worker.whatsapp_id,
            "❌ Partner ID not found. Please check and try again.",
        )
        return {"step": "invalid_partner_id"}

    await db.execute(
        update(Worker)
        .where(Worker.id == worker.id)
        .values(
            partner_id=partner_id.upper().strip(),
            full_name=platform_data["name"],
            phone_number=platform_data["phone"],
            zone=platform_data["zone"],
            onboarding_status=OnboardingStatusEnum.pending_otp,
        )
    )
    await db.commit()

    session = await get_active_session(worker.whatsapp_id, db)
    otp = generate_otp()
    await store_otp(session.id, otp, db)

    await send_text_message(
        worker.whatsapp_id,
        f"✅ Found! Welcome *{platform_data['name']}*!\n\n"
        f"Zone: {platform_data['zone']}\n\n"
        f"Your OTP is: *{otp}*\n\n"
        f"Please reply with this OTP to verify your account.",
    )
    return {"step": "otp_sent"}


async def _step4_verify_otp(
    parsed: ParsedMessage, worker: Worker, db: AsyncSession
) -> dict:
    otp_input = parsed.text
    if not otp_input:
        await send_text_message(
            worker.whatsapp_id,
            "Please enter the OTP sent to you.",
        )
        return {"step": "waiting_otp"}

    session = await get_active_session(worker.whatsapp_id, db)
    is_valid = await verify_otp(session, otp_input, db)

    if not is_valid:
        await send_text_message(
            worker.whatsapp_id,
            "❌ Invalid or expired OTP. Please try again.",
        )
        return {"step": "invalid_otp"}

    # Mark worker as verified
    await db.execute(
        update(Worker)
        .where(Worker.id == worker.id)
        .values(onboarding_status=OnboardingStatusEnum.verified)
    )
    await db.commit()
    await db.refresh(worker)

    # Create first weekly policy
    policy = await create_policy_for_worker(worker, db)

    await send_text_message(
        worker.whatsapp_id,
        f"🎉 You're all set, *{worker.full_name}*!\n\n"
        f"Your GigInsurance account is *active*. ✅\n\n"
        f"📋 *Your Policy*\n"
        f"Coverage: ₹{int(policy.daily_max_payout)}/day\n"
        f"Premium: ₹{float(policy.weekly_premium)}/week\n"
        f"Valid: {policy.week_start.strftime('%d %b')} – {policy.week_end.strftime('%d %b %Y')}\n\n"
        f"If anything disrupts your work — heavy rain, flood, curfew — "
        f"just message me and I'll process your claim instantly. 🚀",
    )
    return {"step": "completed", "policy_id": policy.id}
