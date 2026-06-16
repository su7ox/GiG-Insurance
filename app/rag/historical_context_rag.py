"""Semantic search over past claim text logs and support chats to surface recurring patterns or suspicious timing."""


class HistoricalContextRAG:
    def query(self, worker_id: str, claim_text: str) -> dict:
        raise NotImplementedError
