import enum
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PayoutStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"


class PayoutChannelEnum(str, enum.Enum):
    razorpay = "razorpay"
    upi = "upi"
    wallet = "wallet"


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    amount: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    slf: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    phr: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    channel: Mapped[PayoutChannelEnum] = mapped_column(
        Enum(PayoutChannelEnum, name="payoutchannelenum"),
        nullable=False,
        default=PayoutChannelEnum.razorpay,
    )
    status: Mapped[PayoutStatusEnum] = mapped_column(
        Enum(PayoutStatusEnum, name="payoutstatusenum"),
        nullable=False,
        default=PayoutStatusEnum.pending,
    )

    external_txn_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    settled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    claim: Mapped["Claim"] = relationship(back_populates="payout")
