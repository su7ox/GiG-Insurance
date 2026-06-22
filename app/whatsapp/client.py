"""
WhatsApp client — provider-aware sender.

Provider is selected via the WHATSAPP_PROVIDER env var:
    twilio  → Twilio REST API  (sandbox + production)
    meta    → Meta Graph API   (production, after Business verification)

Defaults to 'twilio' so the sandbox works out of the box.
Interactive buttons (list messages) are not supported by the Twilio
sandbox — they are silently degraded to plain-text equivalents.
"""

import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def _provider() -> str:
    return getattr(settings, "WHATSAPP_PROVIDER", "twilio").lower()


def _twilio_configured() -> bool:
    return bool(
        getattr(settings, "TWILIO_ACCOUNT_SID", "")
        and getattr(settings, "TWILIO_AUTH_TOKEN", "")
        and getattr(settings, "TWILIO_WHATSAPP_FROM", "")
    )


def _meta_configured() -> bool:
    return bool(settings.WHATSAPP_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)


# ── Twilio sender ───────────────────────────────────────────────────────────


async def _twilio_send_text(to: str, message: str) -> dict:
    if not _twilio_configured():
        logger.info(f"[DEV MODE - Twilio] To {to}: {message}")
        return {"status": "dev_mode", "to": to}

    # Ensure E.164 numbers have whatsapp: prefix
    from_number = settings.TWILIO_WHATSAPP_FROM  # e.g. "whatsapp:+14155238886"
    to_number = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={"From": from_number, "To": to_number, "Body": message},
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"Twilio sent to {to_number}: {resp.json().get('sid')}")
        return resp.json()


# ── Meta sender ─────────────────────────────────────────────────────────────

GRAPH_API_URL = "https://graph.facebook.com/v19.0"


async def _meta_send_text(to: str, message: str) -> dict:
    if not _meta_configured():
        logger.info(f"[DEV MODE - Meta] To {to}: {message}")
        return {"status": "dev_mode", "to": to}

    url = f"{GRAPH_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()


async def _meta_send_buttons(to: str, body: str, buttons: list[dict]) -> dict:
    if not _meta_configured():
        logger.info(f"[DEV MODE - Meta] Buttons to {to}: {body}")
        return {"status": "dev_mode"}

    url = f"{GRAPH_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons
                ]
            },
        },
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()


# ── Public API (used everywhere in the app) ─────────────────────────────────


async def send_text_message(to: str, message: str) -> dict:
    if _provider() == "meta":
        return await _meta_send_text(to, message)
    return await _twilio_send_text(to, message)


async def send_interactive_buttons(to: str, body: str, buttons: list[dict]) -> dict:
    """
    Send interactive buttons.
    Twilio sandbox degrades to plain text with numbered options —
    the worker types the number to reply.
    """
    if _provider() == "meta":
        return await _meta_send_buttons(to, body, buttons)

    # Twilio sandbox: no native button support → degrade gracefully
    options = "\n".join(f"{i+1}. {b['title']}" for i, b in enumerate(buttons))
    degraded = f"{body}\n\n{options}\n\n_(Reply with the number of your choice)_"
    logger.info(f"[Twilio] Button degraded to text for {to}")
    return await _twilio_send_text(to, degraded)


async def send_list_message(
    to: str, body: str, button_label: str, sections: list[dict]
) -> dict:
    """
    Send a list picker.
    Twilio sandbox degrades to a numbered plain-text list.
    """
    if _provider() == "meta":
        return await _meta_send_list(to, body, button_label, sections)

    # Flatten sections → numbered list
    lines = [body, ""]
    idx = 1
    for section in sections:
        if section.get("title"):
            lines.append(f"*{section['title']}*")
        for row in section.get("rows", []):
            lines.append(f"{idx}. {row['title']}")
            idx += 1
    lines.append("\n_(Reply with the number of your choice)_")
    return await _twilio_send_text(to, "\n".join(lines))


async def _meta_send_list(
    to: str, body: str, button_label: str, sections: list[dict]
) -> dict:
    if not _meta_configured():
        logger.info(f"[DEV MODE - Meta] List to {to}: {body}")
        return {"status": "dev_mode"}

    url = f"{GRAPH_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "action": {"button": button_label, "sections": sections},
        },
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
