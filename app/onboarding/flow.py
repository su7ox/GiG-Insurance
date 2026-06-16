"""
Conversational onboarding state machine:
Platform Selection -> Partner ID validation -> phone number request -> OTP -> session bound.
"""


class OnboardingFlow:
    def start(self, whatsapp_id: str) -> None:
        raise NotImplementedError

    def handle_step(self, whatsapp_id: str, message: dict) -> None:
        raise NotImplementedError
