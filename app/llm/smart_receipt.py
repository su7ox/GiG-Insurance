from langchain_groq import ChatGroq
from app.config import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are GigInsurance's claim receipt generator.
Generate a brief, friendly WhatsApp claim receipt in 4-5 lines.
Include: disruption type, weather/conditions, decision, payout amount if approved.
Keep it simple, warm, and in the worker's language if specified.
No markdown, no bullets — plain WhatsApp text only."""


async def generate_smart_receipt(
    worker_name: str,
    disruption_type: str,
    decision: str,
    decision_reason: str,
    payout: float | None,
    weather_data: dict | None,
    language: str = "en",
) -> str:
    try:
        context = (
            f"Worker: {worker_name}\n"
            f"Disruption: {disruption_type}\n"
            f"Decision: {decision}\n"
            f"Reason: {decision_reason}\n"
            f"Payout: ₹{payout or 0}\n"
            f"Weather: {weather_data}\n"
            f"Language: {language}"
        )
        llm = ChatGroq(
            model=settings.LLM_MODEL, api_key=settings.GROQ_API_KEY, temperature=0.3
        )
        response = await llm.ainvoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ]
        )
        return response.content.strip()
    except Exception as e:
        logger.error(f"Smart receipt error: {e}")
        return f"Claim {decision}. Reason: {decision_reason}"
