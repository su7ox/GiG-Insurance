import logging

from app.agent.state import ClaimState
from app.rag.retriever import retrieve

logger = logging.getLogger(__name__)

# Deterministic rules used ONLY for eligibility evaluation.
# The policy text itself is retrieved through RAG.
POLICY_RULES = {
    "heavy_rain": {
        "threshold_mm": 50.0,
        "window_hours": 6,
        "description": "Rainfall ≥ 50mm in any 6-hour window qualifies for payout",
    },
    "flood": {
        "threshold_mm": 30.0,
        "window_hours": 3,
        "description": "Rainfall ≥ 30mm in any 3-hour window qualifies",
    },
    "extreme_heat": {
        "threshold_temp_c": 45.0,
        "description": "Temperature ≥ 45°C during active shift hours qualifies",
    },
    "severe_aqi": {
        "threshold_aqi": 300,
        "description": "European AQI ≥ 300 qualifies for payout",
    },
    "cyclone": {
        "threshold_wind_kmh": 60.0,
        "description": "Cyclone warning or wind speed ≥ 60 km/h qualifies",
    },
    "curfew_section_144": {
        "requires_news_confirmation": True,
        "description": "Confirmed government curfew / Section 144 qualifies",
    },
}


async def query_policy_rag(state: ClaimState) -> ClaimState:
    """
    Retrieve the relevant policy sections from ChromaDB.

    RAG is responsible for retrieving policy knowledge.
    It does NOT make the final eligibility decision.
    """

    try:
        disruption_type = state.get("disruption_type", "unknown")

        if disruption_type not in POLICY_RULES:
            state["policy_rule"] = {
                "matched": False,
                "reason": "No covered disruption type found",
            }
            state["steps_completed"].append("query_policy_rag:no_rule")
            return state

        # Query ChromaDB using the actual disruption.
        query = f"""
        GigInsurance policy section for {disruption_type.replace("_", " ")}.
        Find the exact coverage section containing:
        - trigger threshold
        - qualifying conditions
        - payout amount
        - disruption duration
        - exclusions
        """

        chunks = retrieve(query, n_results=6)

        if not chunks:
            state["policy_rule"] = {
                "matched": False,
                "reason": "No relevant policy information retrieved",
                "disruption_type": disruption_type,
            }

            state["steps_completed"].append("query_policy_rag:no_context")
            return state

        # Keep the deterministic rule for the decision engine.
        rule = POLICY_RULES[disruption_type]

        state["policy_rule"] = {
            **rule,
            "disruption_type": disruption_type,
            # Actual RAG output
            "rag_context": "\n\n---\n\n".join(chunks),
            "rag_chunks": chunks,
        }

        state["steps_completed"].append("query_policy_rag:retrieved")

        logger.info(
            f"RAG retrieved {len(chunks)} policy chunks " f"for {disruption_type}"
        )

    except Exception as e:
        logger.error(
            f"Policy RAG error: {e}",
            exc_info=True,
        )

        state["policy_rule"] = {
            "matched": False,
            "reason": f"RAG retrieval failed: {str(e)}",
        }

        state["tool_errors"].append(f"query_policy_rag: {str(e)}")

    return state


def evaluate_policy_threshold(state: ClaimState) -> bool:
    """
    Deterministic eligibility check.

    IMPORTANT:
    The LLM/RAG never decides whether money should be paid.
    This function evaluates the verified data against the
    policy threshold.
    """

    disruption_type = state.get("disruption_type", "unknown")
    rule = state.get("policy_rule", {})
    weather = state.get("weather_data") or {}
    gov_feed = state.get("gov_feed_data") or {}

    if not rule.get("matched", True):
        # If the rule object exists but wasn't matched, deny.
        if "threshold_mm" not in rule and disruption_type != "curfew_section_144":
            return False

    if disruption_type == "heavy_rain":
        return weather.get("rainfall_mm", 0) >= rule.get("threshold_mm", 50)

    elif disruption_type == "flood":
        return weather.get("rainfall_mm", 0) >= rule.get("threshold_mm", 30)

    elif disruption_type == "extreme_heat":
        return weather.get("temp_c", 0) >= rule.get("threshold_temp_c", 45)

    elif disruption_type == "severe_aqi":
        return weather.get("aqi", 0) >= rule.get("threshold_aqi", 300)

    elif disruption_type == "curfew_section_144":
        return gov_feed.get("curfew_detected", False)

    elif disruption_type == "cyclone":
        return weather.get("wind_kmh", 0) >= rule.get("threshold_wind_kmh", 60)

    return False
