"""Pydantic schemas for worker create/read."""
from pydantic import BaseModel


class WorkerCreate(BaseModel):
    platform: str
    partner_id: str
    phone_number: str
