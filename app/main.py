"""
FastAPI entrypoint.

Receives WhatsApp webhook events (Meta / Twilio), routes new users into the
onboarding flow, returning users into the Agentic Claim Processor, and
exposes read-only endpoints consumed by the Admin Dashboard.
"""
from fastapi import FastAPI

from app.api import webhook, admin, health

app = FastAPI(title="GigInsurance API", version="0.1.0")

app.include_router(health.router, tags=["health"])
app.include_router(webhook.router, prefix="/webhook", tags=["whatsapp-webhook"])
app.include_router(admin.router, prefix="/admin", tags=["admin-dashboard"])
