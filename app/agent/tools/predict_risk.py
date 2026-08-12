import logging

from app.agent.state import ClaimState
from app.ml.risk_model import predict_risk_score

logger = logging.getLogger(__name__)


async def predict_claim_risk(
    state: ClaimState,
    historical_risk: float,
) -> ClaimState:
    try:
        weather = state.get("weather_data") or {}

        features = {
            "rainfall_mm": weather.get("rainfall_mm", 0.0),
            "temperature_c": weather.get("temp_c", 0.0),
            "wind_kmh": weather.get("wind_kmh", 0.0),
            "aqi": weather.get("aqi", 0.0),
            "historical_risk": historical_risk,
        }

        risk_score = predict_risk_score(features)

        # Store the XGBoost output in the claim state.
        state["anomaly_score"] = risk_score

        state["steps_completed"].append(
            f"xgboost_risk:predicted_{risk_score}"
        )

        logger.info(
            f"XGBoost risk score: {risk_score} "
            f"from features={features}"
        )

    except Exception as e:
        logger.error(f"XGBoost risk prediction error: {e}")

        state["tool_errors"].append(
            f"xgboost_risk: {str(e)}"
        )

        # Do NOT silently invent a risk score.
        state["anomaly_score"] = None

    return state