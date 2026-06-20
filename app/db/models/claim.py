"""
Claim record.

Captures the worker's raw WhatsApp message, the classified disruption type,
the claimed time window, all agent tool results (stored as JSONB), the
anomaly score from Isolation Forest, and the final agent decision.
"""
import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, Enum as PgEnum, DateTime, func, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DisruptionType(str, enum.Enum):
    heavy_rain = "heavy_rain"
    flood = "flood"
    extreme_heat = "extreme_heat"
    severe_aqi = "severe_aqi"
    cyclone = "cyclone"
    curfew_section_144 = "curfew_section_144"
    unknown = "unknown"


class ClaimDecision(str, enum.Enum):
    approved = "approved"
    denied = "denied"
    manual_review = "manual_review"
    pending = "pending"


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id", ondelete="SET NULL"), nullable=True)

    raw_message: Mapped[str] = mapped_column(Text, nullable=False)          # original WhatsApp text / transcript
    disruption_type: Mapped[DisruptionType] = mapped_column(
        PgEnum(DisruptionType, name="disruption_type_enum"), nullable=False
    )

    claimed_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Agent tool outputs (JSONB for flexibility — each tool writes one key)
    tool_results: Mapped[dict] = mapped_column(JSONB, nullable=True)
    # {
    #   "shift_verified": true,
    #   "weather_data": {...},
    #   "gov_feed": {...},
    #   "policy_rule": {...},
    #   "fraud_history": {...}
    # }

    anomaly_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=True)  # Isolation Forest output
    effective_hours: Mapped[float] = mapped_column(Numeric(4, 2), nullable=True)

    decision: Mapped[ClaimDecision] = mapped_column(
        PgEnum(ClaimDecision, name="claim_decision_enum"),
        default=ClaimDecision.pending,
    )
    decision_reason: Mapped[str] = mapped_column(Text, nullable=True)

    smart_receipt_text: Mapped[str] = mapped_column(Text, nullable=True)   # LLM-generated localized receipt

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    worker: Mapped["Worker"] = relationship(back_populates="claims")
    policy: Mapped["Policy"] = relationship(back_populates="claims")
    payout: Mapped["Payout"] = relationship(back_populates="claim", uselist=False)
