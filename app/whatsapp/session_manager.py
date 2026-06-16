"""
Binds a WhatsApp session to a verified worker profile.

Deleting/clearing the chat thread is treated as an automatic logout: the
backend resets session state and requires phone number + OTP re-verification
before the worker regains access.
"""


def bind_session(whatsapp_id: str, worker_id: str) -> None:
    raise NotImplementedError


def invalidate_session(whatsapp_id: str) -> None:
    raise NotImplementedError
