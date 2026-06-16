"""Typed state object passed between LangGraph nodes for a single claim."""
from typing import TypedDict, Optional


class ClaimAgentState(TypedDict, total=False):
    worker_id: str
    raw_message: str
    disruption_type: Optional[str]
    tool_results: dict
    payout_amount: Optional[float]
    decision: Optional[str]
