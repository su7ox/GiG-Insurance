"""Deterministic payout math: PHR x SLF x Effective Hours, capped at the daily Max Payout."""


def calculate_payout(premium: float, risk_score: float, effective_hours: float, slf: float) -> float:
    raise NotImplementedError
