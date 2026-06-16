"""Pydantic schemas for policy creation/response."""
from pydantic import BaseModel


class PolicyCreate(BaseModel):
    worker_id: int
    weekly_premium: float
