"""Embedding model wrapper shared by both RAG pipelines."""


def embed_text(text: str) -> list[float]:
    raise NotImplementedError
