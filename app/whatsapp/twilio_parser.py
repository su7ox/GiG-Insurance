"""
Parse inbound Twilio WhatsApp Sandbox payloads.

Twilio sends application/x-www-form-urlencoded POST bodies, NOT JSON.
Key fields:
    From      → "whatsapp:+919999999999"
    Body      → raw message text
    To        → Twilio sandbox number
    ButtonText / ButtonPayload  → for quick-reply buttons (Twilio sandbox limited)
"""
from app.whatsapp.message_parser import ParsedMessage
import logging

logger = logging.getLogger(__name__)


def parse_twilio_payload(form: dict) -> ParsedMessage | None:
    """
    Convert a Twilio form-data payload into a ParsedMessage.
    Returns None if the payload has no actionable content.
    """
    try:
        raw_from = form.get("From", "")           # "whatsapp:+919999999999"
        body = (form.get("Body") or "").strip()
        button_payload = (form.get("ButtonPayload") or "").strip()
        button_text = (form.get("ButtonText") or "").strip()

        if not raw_from:
            logger.warning("Twilio payload missing 'From' field")
            return None

        # Strip "whatsapp:" prefix → use the E.164 number as whatsapp_id
        whatsapp_id = raw_from.replace("whatsapp:", "").strip()
        phone_number = whatsapp_id

        # Detect message type
        if button_payload:
            # Quick-reply button tap
            msg_type = "interactive"
            return ParsedMessage(
                whatsapp_id=whatsapp_id,
                phone_number=phone_number,
                msg_type=msg_type,
                text=None,
                button_id=button_payload,        # maps to button "id"
                button_title=button_text,
                list_reply_id=None,
                list_reply_title=None,
                raw=dict(form),
            )

        # Plain text
        if body:
            return ParsedMessage(
                whatsapp_id=whatsapp_id,
                phone_number=phone_number,
                msg_type="text",
                text=body,
                button_id=None,
                button_title=None,
                list_reply_id=None,
                list_reply_title=None,
                raw=dict(form),
            )

        logger.info("Twilio payload has no actionable body")
        return None

    except Exception as e:
        logger.error(f"Twilio payload parse error: {e}")
        return None