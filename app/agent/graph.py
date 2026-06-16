"""
LangGraph definition for the Agentic AI Claim Processor.

Step 1: classify disruption type
Step 2: autonomously call only the relevant tools
Step 3: deterministic payout math (XGBoost + SLF + PHR)
Step 4: final decision -> Approved / Denied / Escalated
"""


def build_claim_agent_graph():
    raise NotImplementedError
