from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    # --- App ---
    APP_NAME: str = "GigInsurance"
    DEBUG: bool = False

    # --- Database ---
    DATABASE_URL: str

    # --- LLM (Groq) ---
    GROQ_API_KEY: str
    LLM_MODEL: str = "llama-3.1-8b-instant"

    # --- Vector DB ---
    CHROMA_PERSIST_DIR: str = "./.chroma"

    # --- Weather API (OpenWeatherMap) ---
    WEATHER_API_KEY: str
    WEATHER_API_BASE_URL: str = "https://api.openweathermap.org"

    # --- Government / News Feed (NewsAPI) ---
    GOV_FEED_API_KEY: str
    GOV_FEED_API_BASE_URL: str = "https://newsapi.org/v2"

    # --- WhatsApp ---
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""

    # --- Payments ---
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # --- Insurance constants ---
    BASE_FEE: float = 20.0
    MAX_DAILY_PAYOUT: float = 500.0
    SOLVENCY_MARGIN: float = 0.10
    SLF_ALPHA: float = 0.5
    PHR_K: float = 0.4
    POLICY_WAITING_PERIOD_HOURS: int = 48

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()