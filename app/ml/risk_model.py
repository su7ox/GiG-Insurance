import os
import xgboost as xgb
import pandas as pd


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "gigshield_risk_model.json",
)

FEATURES = [
    "rainfall_mm",
    "temperature_c",
    "wind_kmh",
    "aqi",
    "historical_risk",
]


_model = None


def _load_model():
    global _model

    if _model is None:
        _model = xgb.XGBRegressor()
        _model.load_model(MODEL_PATH)

    return _model


def predict_risk_score(features: dict) -> float:
    model = _load_model()

    row = {
        feature: float(features.get(feature, 0.0))
        for feature in FEATURES
    }

    X = pd.DataFrame([row], columns=FEATURES)

    prediction = float(model.predict(X)[0])

    return round(max(0.0, min(1.0, prediction)), 4)