"""Issues and verifies OTPs over WhatsApp chat during onboarding/re-authentication."""


def issue_otp(phone_number: str) -> None:
    raise NotImplementedError


def verify_otp(phone_number: str, submitted_code: str) -> bool:
    raise NotImplementedError
