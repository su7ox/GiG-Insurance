import enum
from datetime import datetime, timezone
from sqlalchemy import String, Enum, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PlatformEnum(str, enum.Enum):
    zepto = "zepto"
    blinkit = "blinkit"


class OnboardingStatusEnum(str, enum.Enum):
    pending_platform = "pending_platform"
    pending_partner_id = "pending_partner_id"
    pending_phone = "pending_phone"
    pending_otp = "pending_otp"
    verified = "verified"


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[PlatformEnum] = mapped_column(
        Enum(PlatformEnum, name="platformenum"), nullable=False
    )
    partner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    whatsapp_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    zone: Mapped[str] = mapped_column(String(128), nullable=False)
    vehicle_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tier: Mapped[str | None] = mapped_column(String(16), nullable=True)
    preferred_language: Mapped[str] = mapped_column(
        String(8), nullable=False, default="en"
    )
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    onboarding_status: Mapped[OnboardingStatusEnum] = mapped_column(
        Enum(OnboardingStatusEnum, name="onboardingstatusenum"),
        nullable=False,
        default=OnboardingStatusEnum.pending_platform,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,  # Python sets this before INSERT — never None
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,  # Python sets this before INSERT — never None
        onupdate=_utcnow,  # Python sets this before UPDATE — never None
        nullable=False,
    )

    sessions: Mapped[list["Session"]] = relationship(back_populates="worker")
    policies: Mapped[list["Policy"]] = relationship(back_populates="worker")
    claims: Mapped[list["Claim"]] = relationship(back_populates="worker")
