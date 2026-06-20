"""
Active weekly policy.

Stores the XGBoost-derived risk score, the computed weekly premium
(PHR = risk_score × base_premium), the policy window, status, and
a daily payout cap for this worker-week combination.
"""
import enum
from datetime import datetime, date

from sqlalchemy import ForeignKey, String, Enum as PgEnum, DateTime, Date, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PolicyStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)

    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)   # 0.0 – 1.0
    base_premium: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)  # INR
    weekly_premium: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False) # PHR × base
    daily_max_payout: Mapped[float] = mapped_column(Numeric(8, 2), default=500.0)  # cap in INR

    status: Mapped[PolicyStatus] = mapped_column(
        PgEnum(PolicyStatus, name="policy_status_enum"),
        default=PolicyStatus.active,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    worker: Mapped["Worker"] = relationship(back_populates="policies")
    claims: Mapped[list["Claim"]] = relationship(back_populates="policy")
