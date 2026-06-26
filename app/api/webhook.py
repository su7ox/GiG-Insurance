from chromadb import db
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from app.whatsapp.message_parser import ParsedMessage
from app.rag.policy_qa import answer_policy_question
from app.whatsapp.session_manager import get_worker_by_whatsapp_id
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.db.session import get_db
from app.whatsapp.twilio_parser import parse_twilio_payload
from app.whatsapp.session_manager import (
    is_onboarding_complete,
    get_worker_by_whatsapp_id,
)
from app.onboarding.flow import handle_onboarding
from app.whatsapp.client import send_text_message
from app.agent.classifier import classify_disruption
from app.llm.smart_receipt import generate_smart_receipt
from app.agent.classifier import classify_disruption, is_claim_intent
from app.db.claim_service import save_claim
from app.integrations.platform_api.mock_client import get_worker_profile
from app.agent.graph import claim_graph
from app.integrations.platform_api.mock_client import get_worker_profile
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])


@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Meta webhook verified")
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def receive_message(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        form = await request.form()
        form_dict = dict(form)
        logger.info(f"Twilio inbound: {form_dict}")

        parsed = parse_twilio_payload(form_dict)
        if not parsed:
            return _twiml_response("")

        whatsapp_id = parsed.whatsapp_id
        logger.info(
            f"Message from {whatsapp_id} | type={parsed.msg_type} | text={parsed.text}"
        )

        onboarded = await is_onboarding_complete(whatsapp_id, db)

        if not onboarded:
            result = await handle_onboarding(parsed, db)
            logger.info(f"Onboarding result: {result}")
            return _twiml_response("")

        # Classify before touching claim pipeline
        message_text = parsed.text or ""
        disruption_type = await classify_disruption(message_text)

        if not is_claim_intent(disruption_type):
            await _handle_general_query(whatsapp_id, disruption_type, message_text, db)
            return _twiml_response("")

        # Only real disruptions reach here
        result = await handle_claim(parsed, disruption_type, db)
        logger.info(
            f"Claim decision for {whatsapp_id}: {result.get('decision')} | payout=₹{result.get('final_payout')}"
        )
        return _twiml_response("")

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return _twiml_response("")


async def handle_claim(
    parsed: ParsedMessage, disruption_type: str, db: AsyncSession
) -> dict:
    """Extract claim handling from inline code into a proper function."""
    whatsapp_id = parsed.whatsapp_id
    worker = await get_worker_by_whatsapp_id(whatsapp_id, db)

    initial_state = {
        "whatsapp_id": whatsapp_id,
        "worker_id": worker.id,
        "policy_id": None,
        "raw_message": parsed.text or "",
        "platform": worker.platform.value,
        "partner_id": worker.partner_id,
        "disruption_type": disruption_type,
        "claimed_window_start": None,
        "claimed_window_end": None,
        "shift_verified": None,
        "weather_data": None,
        "gov_feed_data": None,
        "policy_rule": None,
        "fraud_history": None,
        "anomaly_score": None,
        "effective_hours": None,
        "phr": None,
        "slf": None,
        "final_payout": None,
        "decision": None,
        "decision_reason": None,
        "smart_receipt": None,
        "tool_errors": [],
        "steps_completed": [],
    }

    result = await claim_graph.ainvoke(initial_state)
    decision = result.get("decision")
    payout = result.get("final_payout")

    worker_profile = get_worker_profile(worker.platform.value, worker.partner_id)
    worker_name = worker_profile.get("name", "Worker") if worker_profile else "Worker"
    language = (
        worker_profile.get("preferred_language", "en") if worker_profile else "en"
    )

    receipt = await generate_smart_receipt(
        worker_name=worker_name,
        disruption_type=result.get("disruption_type", ""),
        decision=decision,
        decision_reason=result.get("decision_reason", ""),
        payout=payout,
        weather_data=result.get("weather_data"),
        language=language,
    )
    result["smart_receipt"] = receipt
    saved_claim = await save_claim(result, db)
    await send_text_message(whatsapp_id, receipt)
    return result


async def _handle_general_query(
    whatsapp_id: str, intent: str, message_text: str, db: AsyncSession
):
    worker = await get_worker_by_whatsapp_id(whatsapp_id, db)
    worker_name = worker.full_name if worker and worker.full_name else "there"

    if intent == "unknown":
        reply = (
            f"Hi {worker_name}! I'm not sure I understood that. 🤔\n\n"
            "If you're reporting a disruption, describe what happened:\n"
            "e.g. *heavy rain*, *flooding*, *curfew*, *extreme heat*, *bad AQI*\n\n"
            "Or ask me any policy question!"
        )
    else:
        reply = await answer_policy_question(
            question=message_text,
            worker_name=worker_name,
        )

    await send_text_message(whatsapp_id, reply)


def _twiml_response(body: str) -> PlainTextResponse:
    if body:
        xml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{body}</Message></Response>"
    else:
        xml = "<?xml version='1.0' encoding='UTF-8'?><Response></Response>"
    return PlainTextResponse(content=xml, media_type="application/xml")
