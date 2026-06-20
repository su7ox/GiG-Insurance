from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.db.session import get_db
from app.whatsapp.message_parser import parse_whatsapp_payload
from app.whatsapp.session_manager import is_onboarding_complete
from app.onboarding.flow import handle_onboarding
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])


# --- Verification endpoint ---
@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


# --- Incoming message receiver ---
@router.post("/whatsapp")
async def receive_message(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.json()
        logger.info(f"Incoming webhook: {body}")

        parsed = parse_whatsapp_payload(body)
        if not parsed:
            return {"status": "no_actionable_message"}

        whatsapp_id = parsed.whatsapp_id
        logger.info(f"Message from {whatsapp_id} | type={parsed.msg_type} | text={parsed.text}")

        # Route: onboarding or claim agent
        onboarded = await is_onboarding_complete(whatsapp_id, db)

        if not onboarded:
            result = await handle_onboarding(parsed, db)
            return {"status": "onboarding", "result": result}

        # TODO: route to claim agent
        logger.info(f"Worker {whatsapp_id} onboarded — routing to claim agent")
        return {"status": "routed_to_agent", "message": parsed.text}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))