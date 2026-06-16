"""WhatsApp session binding: whatsapp_id <-> worker_id, active/invalidated state."""
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    whatsapp_id: Mapped[str]
    worker_id: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)
