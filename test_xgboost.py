from app.ml.risk_model import predict_risk_score


tests = {
    "normal_weather": {
        "rainfall_mm": 0,
        "temperature_c": 30,
        "wind_kmh": 10,
        "aqi": 50,
        "historical_risk": 0.3,
    },

    "heavy_rain": {
        "rainfall_mm": 84,
        "temperature_c": 25,
        "wind_kmh": 13,
        "aqi": 23,
        "historical_risk": 0.8,
    },

    "extreme_conditions": {
        "rainfall_mm": 90,
        "temperature_c": 47,
        "wind_kmh": 75,
        "aqi": 350,
        "historical_risk": 0.8,
    },
}


for name, features in tests.items():
    score = predict_risk_score(features)

    print(f"{name}: {score}")