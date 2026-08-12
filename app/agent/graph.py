import logging
from langgraph import graph
from langgraph.graph import StateGraph, END
from app.agent.state import ClaimState
from app.agent.tools.verify_shift import verify_active_shift
from app.agent.tools.check_weather import check_weather_api
from app.agent.tools.check_government_feed import check_government_feed
from app.agent.tools.query_policy_rag import query_policy_rag, evaluate_policy_threshold
from app.agent.tools.calculate_payout import calculate_payout
from app.agent.tools.flag_manual_review import flag_for_manual_review
from app.integrations.platform_api.mock_client import get_worker_profile
from app.agent.tools.predict_risk import predict_claim_risk

logger = logging.getLogger(__name__)


async def node_verify_shift(state: ClaimState) -> ClaimState:
    return await verify_active_shift(state, state["partner_id"], state["platform"])


async def node_check_weather(state: ClaimState) -> ClaimState:
    worker = get_worker_profile(state["platform"], state["partner_id"])
    zone = worker["zone"] if worker else "Noida Sector 18"
    return await check_weather_api(state, zone)


async def node_check_gov_feed(state: ClaimState) -> ClaimState:
    worker = get_worker_profile(state["platform"], state["partner_id"])
    zone = worker["zone"] if worker else "Noida Sector 18"
    return await check_government_feed(state, zone)


async def node_query_policy(state: ClaimState) -> ClaimState:
    return await query_policy_rag(state)


async def node_calculate_payout(state: ClaimState) -> ClaimState:
    worker = get_worker_profile(
        state["platform"],
        state["partner_id"]
    )

    weekly_premium = (
        worker.get("weekly_premium", 80.0)
        if worker
        else 80.0
    )

    risk_score = state.get("anomaly_score")

    if risk_score is None:
        state["decision"] = "manual_review"
        state["decision_reason"] = (
            "XGBoost risk prediction was unavailable."
        )
        return state

    return await calculate_payout(
        state,
        risk_score,
        weekly_premium
    )

async def node_make_decision(state: ClaimState) -> ClaimState:
    try:
        if not state.get("shift_verified"):
            state["decision"] = "denied"
            state["decision_reason"] = (
                "Worker was not on an active shift during the claimed window."
            )
            return state

        threshold_met = evaluate_policy_threshold(state)
        if not threshold_met:
            state["decision"] = "denied"
            state["decision_reason"] = (
                "Disruption data did not meet the policy threshold for payout."
            )
            return state

        state["decision"] = "approved"
        state["decision_reason"] = "Shift verified and disruption threshold met."

    except Exception as e:
        logger.error(f"Decision error: {e}")
        state["decision"] = "manual_review"
        state["decision_reason"] = f"Decision error: {str(e)}"

    return state


async def node_flag_review(state: ClaimState) -> ClaimState:
    return await flag_for_manual_review(state)


def route_by_disruption(state: ClaimState) -> str:
    disruption = state.get("disruption_type", "unknown")
    if disruption == "curfew_section_144":
        return "check_gov_feed"
    elif disruption in ("heavy_rain", "flood", "extreme_heat", "severe_aqi", "cyclone"):
        return "check_weather"
    else:
        return "make_decision"


async def node_predict_risk(state: ClaimState) -> ClaimState:
    worker = get_worker_profile(state["platform"], state["partner_id"])

    historical_risk = worker.get("risk_score", 0.5) if worker else 0.5

    return await predict_claim_risk(state, historical_risk)


def build_claim_graph():
    graph = StateGraph(ClaimState)

    graph.add_node("verify_shift", node_verify_shift)
    graph.add_node("check_weather", node_check_weather)
    graph.add_node("check_gov_feed", node_check_gov_feed)
    graph.add_node("query_policy", node_query_policy)
    graph.add_node("predict_risk", node_predict_risk)
    graph.add_node("calculate_payout", node_calculate_payout)
    graph.add_node("make_decision", node_make_decision)
    graph.add_node("flag_review", node_flag_review)

    graph.set_entry_point("verify_shift")

    graph.add_conditional_edges("verify_shift", route_by_disruption)

    graph.add_edge("check_weather", "query_policy")
    graph.add_edge("check_gov_feed", "query_policy")

    graph.add_edge("query_policy", "predict_risk")
    graph.add_edge("predict_risk", "make_decision")

    graph.add_edge("make_decision", "flag_review")

    graph.add_conditional_edges(
        "flag_review",
        lambda s: ("calculate_payout" if s.get("decision") == "approved" else "end"),
        {"calculate_payout": "calculate_payout", "end": END},
    )

    graph.add_edge("calculate_payout", END)

    return graph.compile()


claim_graph = build_claim_graph()
