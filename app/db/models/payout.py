"""
Payout record.

Stores the final computed amount (PHR × SLF × effective_hours, capped at
daily_max_payout), the payment channel, and the external transaction reference
returned by Razorpay / UPI.
"""
import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Enum as PgEnum, DateTime, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PayoutStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"


class PayoutChannel(str, enum.Enum):
    razorpay = "razorpay"
    upi = "upi"
    wallet = "wallet"


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    amount: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)       # final INR amount
    slf: Mapped[float] = mapped_column(Numeric(5, 4), nullable=True)            # Surge Loss Factor applied
    phr: Mapped[float] = mapped_column(Numeric(8, 2), nullable=True)            # Per Hour Rate used

    channel: Mapped[PayoutChannel] = mapped_column(
        PgEnum(PayoutChannel, name="payout_channel_enum"),
        default=PayoutChannel.razorpay,
    )
    status: Mapped[PayoutStatus] = mapped_column(
        PgEnum(PayoutStatus, name="payout_status_enum"),
        default=PayoutStatus.pending,
    )

    external_txn_id: Mapped[str] = mapped_column(String(128), nullable=True)  # Razorpay / UPI ref
    failure_reason: Mapped[str] = mapped_column(String(256), nullable=True)

    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    settled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    claim: Mapped["Claim"] = relationship(back_populates="payout")
