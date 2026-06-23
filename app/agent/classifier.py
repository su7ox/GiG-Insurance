from langchain_groq import ChatGroq
from app.config import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a disruption classifier for an income insurance system for gig delivery workers in India.
Your job is to classify the worker's message into exactly one category.

Categories:
- heavy_rain: Heavy rainfall, flooding, waterlogging preventing delivery
- flood: Flooding, waterlogging, roads submerged
- extreme_heat: Extreme heat above 45°C preventing safe delivery
- severe_aqi: Severe air quality / smog / pollution above AQI 300
- cyclone: Cyclone, storm, strong winds warning
- curfew_section_144: Curfew, Section 144, police blockade, shutdown, bandh
- general_query: Policy questions, account changes, premium queries, greetings, anything NOT a disruption claim
- unknown: Mentions disruption but cannot be classified into any specific type above

Reply with ONLY the category string, nothing else.

Examples:
- "it was raining heavily, couldn't deliver" → heavy_rain
- "police stopped movement near my area" → curfew_section_144
- "roads were flooded" → flood
- "too hot to ride today" → extreme_heat
- "very bad smog today, AQI was terrible" → severe_aqi
- "cyclone warning in my area" → cyclone
- "I want to change my policy" → general_query
- "I want to change my premium policy pricing" → general_query
- "what is my coverage?" → general_query
- "hello" → general_query
- "how do I file a claim?" → general_query
- "something happened today" → unknown
"""

VALID_TYPES = {
    "heavy_rain", "flood", "extreme_heat",
    "severe_aqi", "cyclone", "curfew_section_144",
    "general_query", "unknown",
}

# These are the only types that should enter the claim pipeline
CLAIM_TYPES = {
    "heavy_rain", "flood", "extreme_heat",
    "severe_aqi", "cyclone", "curfew_section_144",
}


async def classify_disruption(message: str) -> str:
    try:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0,
        )
        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ])
        result = response.content.strip().lower()
        if result not in VALID_TYPES:
            logger.warning(f"Unexpected classification: {result} — defaulting to general_query")
            return "general_query"
        logger.info(f"Classified '{message}' → {result}")
        return result
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return "general_query"


def is_claim_intent(disruption_type: str) -> bool:
    """Returns True only if the message should enter the claim pipeline."""
    return disruption_type in CLAIM_TYPES