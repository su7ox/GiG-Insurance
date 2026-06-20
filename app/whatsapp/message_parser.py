from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedMessage:
    whatsapp_id: str
    phone_number: str
    msg_type: str          # text | interactive | audio
    text: Optional[str]    # for text messages
    button_id: Optional[str]   # for interactive button replies
    button_title: Optional[str]
    list_reply_id: Optional[str]   # for list replies
    list_reply_title: Optional[str]
    raw: dict


def parse_whatsapp_payload(body: dict) -> Optional[ParsedMessage]:
    """
    Parse raw WhatsApp webhook payload into a clean ParsedMessage.
    Returns None if payload has no actionable message.
    """
    try:
        entry = body.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        message = messages[0]
        whatsapp_id = message.get("from")
        phone_number = whatsapp_id
        msg_type = message.get("type")

        # --- Plain text ---
        text = None
        if msg_type == "text":
            text = message.get("text", {}).get("body", "").strip()

        # --- Interactive button reply ---
        button_id = None
        button_title = None
        if msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                button_id = interactive["button_reply"].get("id")
                button_title = interactive["button_reply"].get("title")

        # --- Interactive list reply ---
        list_reply_id = None
        list_reply_title = None
        if msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "list_reply":
                list_reply_id = interactive["list_reply"].get("id")
                list_reply_title = interactive["list_reply"].get("title")

        return ParsedMessage(
            whatsapp_id=whatsapp_id,
            phone_number=phone_number,
            msg_type=msg_type,
            text=text,
            button_id=button_id,
            button_title=button_title,
            list_reply_id=list_reply_id,
            list_reply_title=list_reply_title,
            raw=message,
        )

    except Exception:
        return None