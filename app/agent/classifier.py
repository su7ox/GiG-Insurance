from langchain_ollama import ChatOllama
import logging
import re

logger = logging.getLogger(__name__)

QUESTION_PATTERNS = re.compile(
    r"\b("
    r"what|when|how|why|where|which|who|"  # English question words
    r"is there|are there|can i|do i|"
    r"threshold|limit|coverage|policy|premium|"  # Policy-specific terms
    r"payout|eligible|eligib|covered|"
    r"kya|kaise|kitna|kitni|kab|kyun|"  # Hindi question words
    r"mujhe|meri|mera|mere|batao|bata|"
    r"change|update|edit|modify|"  # Account actions
    r"hello|hi|hey|namaste|hii"  # Greetings
    r")\b",
    re.IGNORECASE,
)


def _is_obvious_question(message: str) -> bool:
    """
    Returns True if the message is clearly a question or greeting,
    not a disruption report. Checked before hitting the LLM.
    """
    msg = message.strip()
    if msg.endswith("?"):
        return True
    if QUESTION_PATTERNS.search(msg):
        return True
    return False


SYSTEM_PROMPT = """You are a disruption classifier for an income insurance system for gig delivery workers in India.
Classify the worker's message into exactly one category.

- CRITICAL RULE -
A CLAIM is when the worker is REPORTING that a disruption already happened or is happening NOW.
A QUESTION is when the worker is ASKING about policy, thresholds, coverage, or account details.
Questions about disruption types are ALWAYS general_query, even if they mention rain/AQI/heat.

CLAIM signals: "it was", "there was", "couldn't deliver", "roads were", "today", "happened", "mera area mein hua"
QUESTION signals: "what is", "how much", "threshold", "limit", "kitna", "kya hoga", "?"

Categories:
- heavy_rain       : Worker REPORTS heavy rain prevented their delivery
- flood            : Worker REPORTS flooding/waterlogging prevented delivery  
- extreme_heat     : Worker REPORTS extreme heat (45°C+) prevented delivery
- severe_aqi       : Worker REPORTS terrible air quality prevented delivery
- cyclone          : Worker REPORTS cyclone/storm warning in their area
- curfew_section_144: Worker REPORTS curfew/Section 144 in their area
- general_query    : ANY question, greeting, policy query, account change, or unclear message
- unknown          : Worker clearly reports a disruption but type cannot be identified

Reply with ONLY the category string, nothing else.

EXAMPLES — Claims (disruption happened):
"it was raining heavily, couldn't deliver" → heavy_rain
"roads were flooded near my zone" → flood
"too hot to ride today, 47 degrees" → extreme_heat
"very bad smog today, couldn't breathe" → severe_aqi
"cyclone warning issued in my area" → cyclone
"police curfew declared, couldn't go out" → curfew_section_144
"aaj bahut baarish thi, delivery nahi ho paya" → heavy_rain
"mera area mein paani bhar gaya" → flood
EXAMPLES — Questions (always general_query):
"what is the AQI threshold?" → general_query
"how much should be aqi to get claim?" → general_query
"what is specific threshold for extreme heat?" → general_query
"how much rain is needed for a claim?" → general_query
"what is my daily payout limit?" → general_query
"what are limits for high heat, bad aqi and rain?" → general_query
"under what conditions can I get claims?" → general_query
"I want to change my policy" → general_query
"I want to change my premium pricing" → general_query
"what is my coverage?" → general_query
"hello" → general_query
"how do I file a claim?" → general_query
"kitni baarish honi chahiye claim ke liye?" → general_query
"AQI kitna hona chahiye?" → general_query
"my area heavy rain is 55mm" → general_query
"policy ke anusaar kitna AQI hona chahiye?" → general_query
"something happened today" → unknown
"""
VALID_TYPES = {
    "heavy_rain",
    "flood",
    "extreme_heat",
    "severe_aqi",
    "cyclone",
    "curfew_section_144",
    "general_query",
    "unknown",
}
CLAIM_TYPES = {
    "heavy_rain",
    "flood",
    "extreme_heat",
    "severe_aqi",
    "cyclone",
    "curfew_section_144",
}


async def classify_disruption(message: str) -> str:
    if _is_obvious_question(message):
        logger.info(f"Pre-LLM heuristic: '{message}' → general_query")
        return "general_query"
    try:
        llm = ChatOllama(model="qwen2.5:3b", temperature=0)

        response = await llm.ainvoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ]
        )

        result = response.content.strip().lower()

        if result not in VALID_TYPES:
            logger.warning(
                f"Unexpected classification: '{result}' — "
                "defaulting to general_query"
            )
            return "general_query"

        logger.info(f"LLM classified '{message}' → {result}")
        return result

    except Exception as e:
        logger.error(f"Classification error: {e}")
        return "general_query"


def is_claim_intent(disruption_type: str) -> bool:
    return disruption_type in CLAIM_TYPES
