"""
Policy creation service — called once when a worker completes onboarding.

Risk score formula (simple v1):
    risk_score = BASE_RISK + ZONE_MODIFIER
    weekly_premium = base_premium * (1 + risk_score)

Zone modifiers are placeholder values — replace with real actuarial data.
"""
from datetime import datetime, timezone, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.policy import Policy, PolicyStatusEnum
from app.db.models.worker import Worker
import logging

logger = logging.getLogger(__name__)

# Zone risk modifiers — higher = riskier (flood/rain prone areas)
ZONE_RISK_MAP = {
    "mumbai":     0.30,
    "delhi":      0.20,
    "bangalore":  0.15,
    "chennai":    0.25,
    "kolkata":    0.28,
    "hyderabad":  0.18,
}
DEFAULT_ZONE_RISK = 0.20

BASE_PREMIUM = 20.00       # ₹ per week
DAILY_MAX_PAYOUT = 500.00  # ₹


def _calculate_risk_score(worker: Worker) -> float:
    """Return a 0–1 risk score based on zone."""
    zone_key = (worker.zone or "").lower().strip()
    # Match any zone string that contains a known city
    for city, modifier in ZONE_RISK_MAP.items():
        if city in zone_key:
            return round(min(modifier, 1.0), 4)
    return DEFAULT_ZONE_RISK


def _weekly_premium(risk_score: float) -> float:
    """Premium = base × (1 + risk). Capped at ₹50."""
    return round(min(BASE_PREMIUM * (1 + risk_score), 50.00), 2)


def _policy_window() -> tuple[date, date]:
    """Current week: today → today + 6 days."""
    today = datetime.now(timezone.utc).date()
    return today, today + timedelta(days=6)


async def get_active_policy(worker_id: int, db: AsyncSession) -> Policy | None:
    """Return the worker's current active policy, if any."""
    result = await db.execute(
        select(Policy)
        .where(
            Policy.worker_id == worker_id,
            Policy.status == PolicyStatusEnum.active,
        )
        .order_by(Policy.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_policy_for_worker(worker: Worker, db: AsyncSession) -> Policy:
    """
    Create a new weekly policy for a freshly onboarded worker.
    Idempotent — returns existing active policy if one already exists.
    """
    # Guard: don't create duplicate
    existing = await get_active_policy(worker.id, db)
    if existing:
        logger.info(f"Worker {worker.id} already has active policy {existing.id}")
        return existing

    risk_score = _calculate_risk_score(worker)
    week_start, week_end = _policy_window()
    premium = _weekly_premium(risk_score)

    policy = Policy(
        worker_id=worker.id,
        week_start=week_start,
        week_end=week_end,
        risk_score=risk_score,
        base_premium=BASE_PREMIUM,
        weekly_premium=premium,
        daily_max_payout=DAILY_MAX_PAYOUT,
        status=PolicyStatusEnum.active,
        created_at=datetime.now(timezone.utc),
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    logger.info(
        f"Policy {policy.id} created for worker {worker.id} | "
        f"risk={risk_score} | premium=₹{premium} | "
        f"{week_start} → {week_end}"
    )
    return policy