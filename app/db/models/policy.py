import enum
from datetime import datetime, date
from sqlalchemy import Integer, Float, DateTime, ForeignKey, Date, Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class PolicyStatusEnum(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"
class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column(
        ForeignKey("workers.id", ondelete="CASCADE"), nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    base_premium: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    weekly_premium: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    daily_max_payout: Mapped[float] = mapped_column(
        Numeric(8, 2), nullable=False, default=500.00
    )
    status: Mapped[PolicyStatusEnum] = mapped_column(
        Enum(PolicyStatusEnum, name="policystatusenum"),
        nullable=False,
        default=PolicyStatusEnum.active,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    worker: Mapped["Worker"] = relationship(back_populates="policies")
    claims: Mapped[list["Claim"]] = relationship(back_populates="policy")
