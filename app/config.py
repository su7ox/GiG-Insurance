"""Centralised environment-driven settings (pydantic-settings)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "development"
    app_secret_key: str = "change-me"

    whatsapp_provider: str = "meta"
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/giginsurance"
    chroma_persist_dir: str = "./.chroma"

    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    weather_api_key: str = ""
    weather_api_base_url: str = "https://api.openweathermap.org"
    gov_feed_api_base_url: str = ""
    zepto_mock_api_base_url: str = "http://localhost:8001/mock/zepto"
    blinkit_mock_api_base_url: str = "http://localhost:8001/mock/blinkit"

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    otp_expiry_seconds: int = 300

    class Config:
        env_file = ".env"


settings = Settings()
