from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.db.session import get_db
from app.whatsapp.twilio_parser import parse_twilio_payload
from app.whatsapp.session_manager import is_onboarding_complete
from app.onboarding.flow import handle_onboarding
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])


# Meta webhook verification (keep for future Meta migration)
@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Meta webhook verified")
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


# Twilio WhatsApp Sandbox inbound message handler
@router.post("/whatsapp")
async def receive_message(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        # Twilio sends application/x-www-form-urlencoded, NOT JSON
        form = await request.form()
        form_dict = dict(form)
        logger.info(f"Twilio inbound: {form_dict}")

        parsed = parse_twilio_payload(form_dict)
        if not parsed:
            # Always return 200 to Twilio even for status callbacks
            return _twiml_response("")

        whatsapp_id = parsed.whatsapp_id
        logger.info(
            f"Message from {whatsapp_id} | type={parsed.msg_type} | text={parsed.text}"
        )

        onboarded = await is_onboarding_complete(whatsapp_id, db)

        if not onboarded:
            result = await handle_onboarding(parsed, db)
            logger.info(f"Onboarding result: {result}")
            return _twiml_response("")   # actual reply sent via send_text_message()

        # TODO: route to claim agent
        logger.info(f"Worker {whatsapp_id} onboarded — routing to claim agent")
        return _twiml_response("")

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _twiml_response(body: str) -> PlainTextResponse:
    """
    Minimal TwiML 200 response.
    Replies are sent proactively via the Twilio REST API (send_text_message),
    so TwiML body is empty unless we want to reply inline.
    """
    if body:
        xml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{body}</Message></Response>"
    else:
        xml = "<?xml version='1.0' encoding='UTF-8'?><Response></Response>"
    return PlainTextResponse(content=xml, media_type="application/xml")