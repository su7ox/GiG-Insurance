import os
import numpy as np
import pandas as pd
import xgboost as xgb


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data", "ml")
MODEL_DIR = os.path.join(BASE_DIR, "app", "ml", "models")

CSV_PATH = os.path.join(DATA_DIR, "risk_training.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "gigshield_risk_model.json")


FEATURES = [
    "rainfall_mm",
    "temperature_c",
    "wind_kmh",
    "aqi",
    "historical_risk",
]


def generate_training_data(n=3000):
    rng = np.random.default_rng(42)

    rainfall = rng.uniform(0, 100, n)
    temperature = rng.uniform(20, 50, n)
    wind = rng.uniform(0, 100, n)
    aqi = rng.uniform(0, 500, n)
    historical_risk = rng.uniform(0.1, 0.9, n)

    # Synthetic disruption-risk relationship.
    rain_risk = np.clip(rainfall / 50, 0, 1)
    heat_risk = np.clip((temperature - 35) / 15, 0, 1)
    wind_risk = np.clip(wind / 80, 0, 1)
    aqi_risk = np.clip(aqi / 300, 0, 1)

    risk = (
        0.35 * rain_risk
        + 0.20 * heat_risk
        + 0.15 * wind_risk
        + 0.20 * aqi_risk
        + 0.10 * historical_risk
    )

    # Add small noise so the model learns a pattern rather than
    # reproducing one exact mathematical formula.
    risk += rng.normal(0, 0.03, n)

    risk = np.clip(risk, 0, 1)

    return pd.DataFrame({
        "rainfall_mm": rainfall,
        "temperature_c": temperature,
        "wind_kmh": wind,
        "aqi": aqi,
        "historical_risk": historical_risk,
        "risk_score": risk,
    })


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    df = generate_training_data()

    df.to_csv(CSV_PATH, index=False)

    X = df[FEATURES]
    y = df["risk_score"]

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
    )

    model.fit(X, y)

    model.save_model(MODEL_PATH)

    print("Training completed.")
    print(f"Dataset: {CSV_PATH}")
    print(f"Rows: {len(df)}")
    print(f"Model: {MODEL_PATH}")

    print("\nFeature importance:")
    for feature, importance in zip(FEATURES, model.feature_importances_):
        print(f"{feature}: {importance:.4f}")


if __name__ == "__main__":
    main()