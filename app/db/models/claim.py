import enum
from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class DisruptionTypeEnum(str, enum.Enum):
    heavy_rain = "heavy_rain"
    flood = "flood"
    extreme_heat = "extreme_heat"
    severe_aqi = "severe_aqi"
    cyclone = "cyclone"
    curfew_section_144 = "curfew_section_144"
    unknown = "unknown"


class ClaimDecisionEnum(str, enum.Enum):
    approved = "approved"
    denied = "denied"
    manual_review = "manual_review"
    pending = "pending"


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column(
        ForeignKey("workers.id", ondelete="CASCADE"), nullable=False
    )
    policy_id: Mapped[int | None] = mapped_column(
        ForeignKey("policies.id", ondelete="SET NULL"), nullable=True
    )
    raw_message: Mapped[str] = mapped_column(Text, nullable=False)
    disruption_type: Mapped[DisruptionTypeEnum] = mapped_column(
        Enum(DisruptionTypeEnum, name="disruptiontypeenum"), nullable=False
    )
    claimed_window_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    claimed_window_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tool_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    anomaly_score: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    effective_hours: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    decision: Mapped[ClaimDecisionEnum] = mapped_column(
        Enum(ClaimDecisionEnum, name="claimdecisionenum"),
        nullable=False,
        default=ClaimDecisionEnum.pending,
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    smart_receipt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    worker: Mapped["Worker"] = relationship(back_populates="claims")
    policy: Mapped["Policy"] = relationship(back_populates="claims")
    payout: Mapped["Payout"] = relationship(back_populates="claim", uselist=False)
