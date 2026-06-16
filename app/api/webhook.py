"""
WhatsApp webhook receiver.

Single inbound endpoint for Meta/Twilio. Verifies the request, then routes
the message to onboarding (new user) or the Claim Agent (returning user)
based on session state.
"""
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/")
async def verify_webhook(request: Request):
    """Meta webhook verification handshake (hub.challenge)."""
    raise NotImplementedError


@router.post("/")
async def receive_message(request: Request):
    """Entry point for every inbound WhatsApp message/button/list event."""
    raise NotImplementedError
