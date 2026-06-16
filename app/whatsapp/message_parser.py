"""Normalises inbound payloads (text / voice transcript / button / list) into a single internal message schema."""


def parse_inbound_payload(raw_payload: dict) -> dict:
    raise NotImplementedError
