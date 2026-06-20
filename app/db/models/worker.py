"""
Worker profile.

Stores the gig worker's platform (zepto | blinkit), partner ID validated
against the platform mock API, verified phone number (used for OTP binding),
WhatsApp ID, delivery zone, and onboarding/verification state.
"""
import enum
from datetime import datetime

from sqlalchemy import String, Enum as PgEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Platform(str, enum.Enum):
    zepto = "zepto"
    blinkit = "blinkit"


class OnboardingStatus(str, enum.Enum):
    pending_platform = "pending_platform"
    pending_partner_id = "pending_partner_id"
    pending_phone = "pending_phone"
    pending_otp = "pending_otp"
    verified = "verified"


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    platform: Mapped[Platform] = mapped_column(PgEnum(Platform, name="platform_enum"), nullable=False)
    partner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    whatsapp_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    zone: Mapped[str] = mapped_column(String(128), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(32), nullable=True)   # bicycle | motorcycle | e-bike
    tier: Mapped[str] = mapped_column(String(16), nullable=True)           # bronze | silver | gold
    preferred_language: Mapped[str] = mapped_column(String(8), default="en")  # en | hi | mr | te

    onboarding_status: Mapped[OnboardingStatus] = mapped_column(
        PgEnum(OnboardingStatus, name="onboarding_status_enum"),
        default=OnboardingStatus.pending_platform,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    policies: Mapped[list["Policy"]] = relationship(back_populates="worker")
    claims: Mapped[list["Claim"]] = relationship(back_populates="worker")
    sessions: Mapped[list["Session"]] = relationship(back_populates="worker")
