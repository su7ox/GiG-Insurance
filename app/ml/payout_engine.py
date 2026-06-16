"""
Step-by-step payout calculation:
PHR -> Effective Hours -> Adjusted Rate (SLF) -> Final Payout (capped at the daily max).
"""


def compute_phr(premium: float, risk_score: float, k: float = 0.4) -> float:
    raise NotImplementedError


def compute_slf(claim_density: float, alpha: float = 0.5) -> float:
    raise NotImplementedError


def compute_final_payout(adjusted_rate: float, effective_hours: float, max_payout: float = 500.0) -> float:
    raise NotImplementedError
