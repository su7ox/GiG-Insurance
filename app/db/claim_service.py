from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.claim import Claim, DisruptionTypeEnum, ClaimDecisionEnum
from app.db.models.payout import Payout, PayoutStatusEnum, PayoutChannelEnum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def save_claim(state: dict, db: AsyncSession) -> Claim:
    try:
        disruption = state.get("disruption_type", "unknown")
        if disruption not in [e.value for e in DisruptionTypeEnum]:
            disruption = "unknown"

        decision = state.get("decision", "pending")
        if decision not in [e.value for e in ClaimDecisionEnum]:
            decision = "pending"

        claim = Claim(
            worker_id=state["worker_id"],
            policy_id=state.get("policy_id"),
            raw_message=state["raw_message"],
            disruption_type=DisruptionTypeEnum(disruption),
            tool_results={
                "shift_verified": state.get("shift_verified"),
                "weather": state.get("weather_data"),
                "gov_feed": state.get("gov_feed_data"),
                "policy_rule": state.get("policy_rule"),
            },
            anomaly_score=state.get("anomaly_score"),
            effective_hours=state.get("effective_hours"),
            decision=ClaimDecisionEnum(decision),
            decision_reason=state.get("decision_reason"),
            smart_receipt_text=state.get("smart_receipt"),
            created_at=datetime.utcnow(),
            resolved_at=(
                datetime.utcnow() if decision in ("approved", "denied") else None
            ),
        )
        db.add(claim)
        await db.flush()

        if decision == "approved" and state.get("final_payout"):
            payout = Payout(
                claim_id=claim.id,
                amount=state["final_payout"],
                slf=state.get("slf"),
                phr=state.get("phr"),
                channel=PayoutChannelEnum.wallet,
                status=PayoutStatusEnum.pending,
                initiated_at=datetime.utcnow(),
            )
            db.add(payout)

        await db.commit()
        await db.refresh(claim)
        logger.info(f"Claim saved: id={claim.id} decision={decision}")
        return claim

    except Exception as e:
        await db.rollback()
        logger.error(f"Save claim error: {e}")
        raise
