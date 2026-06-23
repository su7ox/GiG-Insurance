from app.whatsapp.message_parser import ParsedMessage


def parse_twilio_payload(form_data: dict) -> ParsedMessage | None:
    try:
        whatsapp_id = (
            form_data.get("From", "").replace("whatsapp:", "").replace("+", "")
        )
        text = form_data.get("Body", "").strip()

        if not whatsapp_id:
            return None

        return ParsedMessage(
            whatsapp_id=whatsapp_id,
            phone_number=whatsapp_id,
            msg_type="text",
            text=text,
            button_id=None,
            button_title=None,
            list_reply_id=None,
            list_reply_title=None,
            raw=form_data,
        )
    except Exception:
        return None
