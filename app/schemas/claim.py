"""Pydantic schemas for claim submission/response."""
from pydantic import BaseModel


class ClaimSubmission(BaseModel):
    worker_id: int
    message: str
