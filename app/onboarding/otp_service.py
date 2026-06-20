import random
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.db.models.session import Session
import logging

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def otp_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)


async def store_otp(session_id, otp: str, db: AsyncSession) -> None:
    print(f"🔑 OTP for session {session_id}: {otp}", flush=True)
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(
            pending_otp_hash=hash_otp(otp),
            otp_expires_at=otp_expires_at(),
        )
    )
    await db.commit()
    logger.info(f"OTP stored for session {session_id}")


async def verify_otp(session: Session, otp_input: str, db: AsyncSession) -> bool:
    if not session.pending_otp_hash or not session.otp_expires_at:
        return False

    now = datetime.now(timezone.utc)
    expires = session.otp_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        logger.warning(f"OTP expired for session {session.id}")
        return False
    return session.pending_otp_hash == hash_otp(otp_input.strip())
