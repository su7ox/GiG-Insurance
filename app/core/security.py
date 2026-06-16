"""OTP generation/validation and session-token helpers."""


def generate_otp() -> str:
    raise NotImplementedError


def verify_otp(submitted: str, expected: str) -> bool:
    raise NotImplementedError
