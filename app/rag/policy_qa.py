
from langchain_ollama import ChatOllama
from app.rag.retriever import retrieve
from app.config import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful insurance assistant for GigInsurance,
an income protection service for gig delivery workers in India (Zepto & Blinkit).

LANGUAGE RULE — STRICT:
Reply ONLY in {language}. Do not switch languages under any circumstances.
If language is "en" → English only.
If language is "hi" → Hindi only.

Answer the worker's question using ONLY the policy information provided below.
Be concise, friendly, and use simple language.
Use ₹ for amounts. If the answer isn't in the policy context, say so honestly.
Never make up coverage amounts, thresholds, or payout values.

POLICY CONTEXT:
{context}
"""


def _detect_language(message: str) -> str:
    """
    Detect language from the current message.
    Returns 'hi' for Hindi, 'en' for English.
    """
    hindi_chars = set("अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह")
    hindi_words = {
        "aap",
        "hai",
        "hain",
        "kya",
        "mera",
        "meri",
        "mere",
        "nahi",
        "aaj",
        "kal",
        "kaise",
        "kitna",
        "kitni",
        "baarish",
        "thi",
        "tha",
        "ke",
        "ki",
        "ka",
        "ko",
        "se",
        "mein",
        "par",
        "aur",
        "ya",
        "bhi",
        "bahut",
        "thoda",
        "jab",
        "tab",
        "agar",
        "to",
        "lekin",
        "aur",
    }
    words = message.lower().split()
    # Check for Devanagari script
    if any(c in hindi_chars for c in message):
        return "hi"
    # Check for Hindi romanized words
    hindi_count = sum(1 for w in words if w in hindi_words)
    if hindi_count >= 2 or (len(words) > 0 and hindi_count / len(words) > 0.3):
        return "hi"
    return "en"


async def answer_policy_question(
    question: str,
    worker_name: str = "there",
    preferred_language: str = "en",
) -> str:
    """
    Retrieve relevant policy chunks and generate a grounded answer.

    preferred_language: "en" or "hi" — stored on worker record.
    Overridden if the current message is clearly in one language.
    """
    try:
        # Current message language takes priority over stored preference
        current_lang = _detect_language(question)
        language = current_lang if current_lang == "en" else preferred_language

        # Retrieve more chunks for multi-topic queries
        # Count distinct topics in the question to scale retrieval
        topic_keywords = [
            "heat",
            "aqi",
            "rain",
            "flood",
            "cyclone",
            "curfew",
            "garmi",
            "baarish",
            "paani",
        ]
        topic_count = sum(1 for kw in topic_keywords if kw in question.lower())
        n_results = max(4, min(topic_count * 2 + 2, 8))  # 4–8 chunks

        chunks = retrieve(question, n_results=n_results)
        if not chunks:
            return (
                f"Sorry {worker_name}, I couldn't find that information. "
                f"Please contact support@giginsurance.in 📧"
            )

        context = "\n\n---\n\n".join(chunks)
        lang_label = "English" if language == "en" else "Hindi"

        llm = ChatOllama(
            model="qwen2.5:3b",
            temperature=0.1,
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(
                    context=context,
                    language=lang_label,
                ),
            },
            {
                "role": "user",
                "content": f"Worker name: {worker_name}\nQuestion: {question}",
            },
        ]

        response = await llm.ainvoke(messages)
        answer = response.content.strip()
        logger.info(
            f"RAG answered in {lang_label} for {worker_name}: '{question[:50]}'"
        )
        return answer

    except Exception as e:
        logger.error(f"Policy QA error: {e}")
        return (
            "Sorry, I'm having trouble answering that right now. "
            "Please contact support@giginsurance.in 📧"
        )
