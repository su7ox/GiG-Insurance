import httpx
import logging
from app.agent.state import ClaimState

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
AQI_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

DEFAULT_COORDS = (28.6139, 77.2090)  # New Delhi fallback


async def resolve_zone_coords(zone: str) -> tuple[float, float]:
    try:
        city = zone.split()[0]
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                GEOCODING_URL,
                params={"name": city, "count": 5, "language": "en", "format": "json"},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            india = [x for x in results if x.get("country_code") == "IN"]
            if india:
                lat = india[0]["latitude"]
                lon = india[0]["longitude"]
                logger.info(f"Resolved '{zone}' → ({lat}, {lon})")
                return lat, lon
    except Exception as e:
        logger.warning(f"Geocoding failed for '{zone}': {e}", exc_info=True)
    logger.warning(f"Using default coords for '{zone}'")
    return DEFAULT_COORDS


async def check_weather_api(state: ClaimState, zone: str) -> ClaimState:
    try:
        lat, lon = await resolve_zone_coords(zone)

        async with httpx.AsyncClient() as client:
            weather_resp = await client.get(
                OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": [
                        "temperature_2m",
                        "precipitation",
                        "rain",
                        "weathercode",
                        "windspeed_10m",
                    ],
                    "timezone": "Asia/Kolkata",
                },
                timeout=10,
            )
            weather_resp.raise_for_status()
            weather = weather_resp.json()

            aqi_resp = await client.get(
                AQI_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": ["european_aqi", "pm2_5", "pm10"],
                    "timezone": "Asia/Kolkata",
                },
                timeout=10,
            )
            aqi_resp.raise_for_status()
            aqi_data = aqi_resp.json()

        current = weather.get("current", {})
        aqi_current = aqi_data.get("current", {})

        rainfall_mm = current.get("rain", 0.0) or current.get("precipitation", 0.0)
        temp_c = current.get("temperature_2m")
        wind_kmh = current.get("windspeed_10m")
        weather_code = current.get("weathercode")
        aqi = aqi_current.get("european_aqi")
        pm2_5 = aqi_current.get("pm2_5")

        state["weather_data"] = {
            "rainfall_mm": rainfall_mm,
            "temp_c": temp_c,
            "wind_kmh": wind_kmh,
            "weather_code": weather_code,
            "aqi": aqi,
            "pm2_5": pm2_5,
            "zone": zone,
            "coords": {"lat": lat, "lon": lon},
        }
        state["steps_completed"].append("check_weather:fetched")
        logger.info(
            f"Weather for {zone}: rain={rainfall_mm}mm temp={temp_c}°C aqi={aqi} wind={wind_kmh}km/h"
        )

    except Exception as e:
        logger.error(f"Weather API error: {e}", exc_info=True)
        state["weather_data"] = {"rainfall_mm": 0, "temp_c": None, "aqi": None}
        state["tool_errors"].append(f"check_weather: {str(e)}")

    return state
