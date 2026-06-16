"""
Thin wrapper around the Meta WhatsApp Cloud API / Twilio API.
Sends text, voice-transcribed text, interactive buttons, and list messages.
"""


class WhatsAppClient:
    def send_text(self, to: str, body: str) -> None:
        raise NotImplementedError

    def send_buttons(self, to: str, body: str, options: list[str]) -> None:
        raise NotImplementedError

    def send_list(self, to: str, body: str, items: list[str]) -> None:
        raise NotImplementedError
