"""Claim record: disruption type, window, tool results, decision."""
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int]
    disruption_type: Mapped[str]
    decision: Mapped[str]
