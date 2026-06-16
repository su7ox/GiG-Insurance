"""Active weekly policy: premium, risk score, base fee, tier."""
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int]
    weekly_premium: Mapped[float]
    risk_score: Mapped[float]
