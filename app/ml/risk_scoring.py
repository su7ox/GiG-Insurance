from app.ml.risk_model import predict_risk_score


def calculate_risk_score(
    rainfall_mm: float,
    temperature_c: float,
    wind_kmh: float,
    aqi: float,
    historical_risk: float,
) -> float:

    features = {
        "rainfall_mm": rainfall_mm,
        "temperature_c": temperature_c,
        "wind_kmh": wind_kmh,
        "aqi": aqi,
        "historical_risk": historical_risk,
    }

    return predict_risk_score(features)