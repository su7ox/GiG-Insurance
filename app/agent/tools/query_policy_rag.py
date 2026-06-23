import logging
from app.agent.state import ClaimState
logger = logging.getLogger(__name__)
POLICY_RULES = {
    "heavy_rain": {
        "threshold_mm": 50.0,
        "window_hours": 6,
        "description": "Rainfall exceeding 50mm in 6 hours qualifies for payout",
    },
    "flood": {
        "threshold_mm": 30.0,
        "window_hours": 3,
        "description": "Waterlogging with 30mm+ rainfall in 3 hours qualifies",
    },
    "extreme_heat": {
        "threshold_temp_c": 45.0,
        "description": "Temperature exceeding 45°C qualifies for payout",
    },
    "severe_aqi": {
        "threshold_aqi": 300,
        "description": "AQI exceeding 300 qualifies for payout",
    },
    "cyclone": {
        "threshold_wind_kmh": 60,
        "description": "Cyclone/storm warning with winds above 60km/h qualifies",
    },
    "curfew_section_144": {
        "requires_news_confirmation": True,
        "description": "Confirmed curfew/Section 144 in worker zone qualifies",
    },
}

async def query_policy_rag(state: ClaimState) -> ClaimState:
    try:
        disruption_type = state.get("disruption_type", "unknown")
        rule = POLICY_RULES.get(disruption_type)

        if not rule:
            state["policy_rule"] = {"matched": False, "reason": "No policy rule found"}
            state["steps_completed"].append("query_policy_rag:no_rule")
            return state

        state["policy_rule"] = {**rule, "disruption_type": disruption_type}
        state["steps_completed"].append("query_policy_rag:fetched")
        logger.info(f"Policy rule fetched for {disruption_type}")
    except Exception as e:
        logger.error(f"Policy RAG error: {e}")
        state["policy_rule"] = {"matched": False}
        state["tool_errors"].append(f"query_policy_rag: {str(e)}")
    return state
def evaluate_policy_threshold(state: ClaimState) -> bool:
    disruption_type = state.get("disruption_type", "unknown")
    rule = state.get("policy_rule", {})
    weather = state.get("weather_data", {})
    gov_feed = state.get("gov_feed_data", {})

    if disruption_type in ("heavy_rain", "flood"):
        return weather.get("rainfall_mm", 0) >= rule.get("threshold_mm", 50)
    elif disruption_type == "extreme_heat":
        return weather.get("temp_c", 0) >= rule.get("threshold_temp_c", 45)
    elif disruption_type == "severe_aqi":
        return weather.get("aqi", 0) >= rule.get("threshold_aqi", 300)
    elif disruption_type == "curfew_section_144":
        return gov_feed.get("curfew_detected", False)
    elif disruption_type == "cyclone":
        return True
    return False