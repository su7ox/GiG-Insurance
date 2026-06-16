"""
LLM synthesis layer (communication only, never decision-making).
Generates a localized Smart Receipt (Hindi / Marathi / Telugu) from the
agent's Context Packet: policy rule retrieved, sensor readings, shift
verification result, and final payout math.
"""


def generate_smart_receipt(context_packet: dict, language: str) -> str:
    raise NotImplementedError
