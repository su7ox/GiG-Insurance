"""
Retrieve relevant policy chunks from ChromaDB.
"""
import chromadb
from chromadb.utils import embedding_functions
import os
import logging

logger = logging.getLogger(__name__)

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./.chroma")
COLLECTION_NAME = "giginsurance_policy"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        _collection = _client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
        )
    return _collection


def retrieve(query: str, n_results: int = 4) -> list[str]:
    """
    Retrieve top-n relevant policy chunks for a query.
    Returns list of text chunks, most relevant first.
    """
    try:
        collection = _get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        chunks = results["documents"][0] if results["documents"] else []
        logger.info(f"RAG retrieved {len(chunks)} chunks for: '{query}'")
        return chunks
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return []
