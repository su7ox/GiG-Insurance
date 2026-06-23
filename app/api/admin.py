from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models.claim import Claim, ClaimDecisionEnum
from app.db.models.payout import Payout
from app.db.models.worker import Worker
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Total claims
    total = await db.execute(select(func.count(Claim.id)))
    total_claims = total.scalar()

    # Claims by decision
    approved = await db.execute(select(func.count(Claim.id)).where(Claim.decision == ClaimDecisionEnum.approved))
    denied = await db.execute(select(func.count(Claim.id)).where(Claim.decision == ClaimDecisionEnum.denied))
    manual = await db.execute(select(func.count(Claim.id)).where(Claim.decision == ClaimDecisionEnum.manual_review))

    # Total payouts
    payout_total = await db.execute(select(func.sum(Payout.amount)))

    # Total workers
    workers = await db.execute(select(func.count(Worker.id)))

    return {
        "total_claims": total_claims,
        "approved": approved.scalar(),
        "denied": denied.scalar(),
        "manual_review": manual.scalar(),
        "total_payout_inr": float(payout_total.scalar() or 0),
        "total_workers": workers.scalar(),
    }


@router.get("/claims")
async def get_claims(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Claim).order_by(Claim.created_at.desc()).limit(50)
    )
    claims = result.scalars().all()
    return [
        {
            "id": c.id,
            "worker_id": c.worker_id,
            "disruption_type": c.disruption_type.value,
            "decision": c.decision.value,
            "decision_reason": c.decision_reason,
            "anomaly_score": c.anomaly_score,
            "tool_results": c.tool_results,
            "smart_receipt_text": c.smart_receipt_text,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in claims
    ]


@router.get("/manual-review")
async def get_manual_review(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Claim).where(Claim.decision == ClaimDecisionEnum.manual_review).order_by(Claim.created_at.desc())
    )
    claims = result.scalars().all()
    return [
        {
            "id": c.id,
            "worker_id": c.worker_id,
            "disruption_type": c.disruption_type.value,
            "decision_reason": c.decision_reason,
            "anomaly_score": float(c.anomaly_score) if c.anomaly_score else None,
            "tool_results": c.tool_results,
            "raw_message": c.raw_message,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in claims
    ]


@router.get("/loss-ratio")
async def get_loss_ratio(db: AsyncSession = Depends(get_db)):
    from app.db.models.policy import Policy
    premiums = await db.execute(select(func.sum(Policy.weekly_premium)))
    payouts = await db.execute(select(func.sum(Payout.amount)))
    total_premium = float(premiums.scalar() or 1)
    total_payout = float(payouts.scalar() or 0)
    return {
        "total_premium_collected": total_premium,
        "total_payout_disbursed": total_payout,
        "loss_ratio": round(total_payout / total_premium, 4),
    }