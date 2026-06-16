"""Worker profile: platform, partner_id, zone, verified phone number, WhatsApp session id."""
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str]
    partner_id: Mapped[str]
    phone_number: Mapped[str]
    zone: Mapped[str]
