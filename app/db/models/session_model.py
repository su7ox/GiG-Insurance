"""
WhatsApp session binding.

Maps a WhatsApp ID to a verified worker profile. Deleting or clearing the
WhatsApp chat thread triggers session invalidation; the worker must re-verify
their phone number + OTP before regaining access.

Also stores pending OTP state so the onboarding flow can resume after the
user sends the code back.
"""
from datetime import datetime

from sqlalchemy import ForeignKey, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    whatsapp_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    worker_id: Mapped[int] = mapped_column(
        ForeignKey("workers.id", ondelete="CASCADE"), nullable=True  # NULL until onboarding complete
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # OTP state — cleared once verified
    pending_otp_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    otp_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    otp_attempts: Mapped[int] = mapped_column(default=0)

    # Onboarding progress (mirrors Worker.onboarding_status for quick lookup without a join)
    onboarding_step: Mapped[str] = mapped_column(String(32), default="pending_platform")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    invalidated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    worker: Mapped["Worker"] = relationship(back_populates="sessions")
