from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models.session import Session
from app.db.models.worker import Worker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def get_active_session(whatsapp_id: str, db: AsyncSession) -> Session | None:
    result = await db.execute(select(Session).where(Session.whatsapp_id == whatsapp_id))
    return result.scalars().first()


async def get_worker_by_whatsapp_id(
    whatsapp_id: str, db: AsyncSession
) -> Worker | None:
    result = await db.execute(select(Worker).where(Worker.whatsapp_id == whatsapp_id))
    return result.scalars().first()


async def invalidate_session(whatsapp_id: str, db: AsyncSession) -> None:
    await db.execute(
        update(Session)
        .where(Session.whatsapp_id == whatsapp_id)
        .values(is_active=False, invalidated_at=datetime.utcnow())
    )
    await db.commit()
    logger.info(f"Session invalidated for {whatsapp_id}")


async def create_session(worker_id: int, whatsapp_id: str, db: AsyncSession) -> Session:
    # Check if session already exists for this whatsapp_id
    existing = await get_active_session(whatsapp_id, db)
    if existing:
        return existing

    session = Session(
        worker_id=worker_id,
        whatsapp_id=whatsapp_id,
        is_active=True,
        onboarding_step="pending_platform",
        last_active_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info(f"New session created for {whatsapp_id}")
    return session


async def is_onboarding_complete(whatsapp_id: str, db: AsyncSession) -> bool:
    worker = await get_worker_by_whatsapp_id(whatsapp_id, db)
    if not worker:
        return False
    return worker.onboarding_status.value == "verified"
