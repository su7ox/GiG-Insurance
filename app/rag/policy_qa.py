"""
Answer worker policy questions using RAG over policy documents.
Called when classifier returns general_query.
"""
from langchain_groq import ChatGroq
from app.rag.retriever import retrieve
from app.config import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful insurance assistant for GigInsurance, 
an income protection service for gig delivery workers in India (Zepto & Blinkit).

Answer the worker's question using ONLY the policy information provided below.
Be concise, friendly, and use simple language (workers may not be highly educated).
Use ₹ for amounts. If the answer isn't in the policy context, say so honestly.
Never make up coverage amounts, thresholds, or payout values.
Respond in the same language the worker used (Hindi or English).

POLICY CONTEXT:
{context}
"""


async def answer_policy_question(question: str, worker_name: str = "there") -> str:
    """
    Retrieve relevant policy chunks and generate a grounded answer.
    """
    try:
        # Retrieve relevant chunks
        chunks = retrieve(question, n_results=4)
        if not chunks:
            return (
                f"Sorry {worker_name}, I couldn't find that information right now. "
                f"Please contact support at support@giginsurance.in 📧"
            )

        context = "\n\n---\n\n".join(chunks)

        llm = ChatGroq(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.1,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
            {"role": "user", "content": f"Worker name: {worker_name}\nQuestion: {question}"},
        ]

        response = await llm.ainvoke(messages)
        answer = response.content.strip()
        logger.info(f"RAG answered query for {worker_name}: '{question[:50]}...'")
        return answer

    except Exception as e:
        logger.error(f"Policy QA error: {e}")
        return (
            "Sorry, I'm having trouble answering that right now. "
            "Please contact support@giginsurance.in 📧"
        )
