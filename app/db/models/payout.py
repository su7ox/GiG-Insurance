"""Payout record linked to a claim, with amount and payment channel reference."""
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int]
    amount: Mapped[float]
