"""Vector search over chunked insurance contract PDFs, filtered by worker tier, vehicle type, and disruption category."""


class PolicyRAG:
    def query(self, tier: str, vehicle_type: str, disruption_type: str) -> dict:
        raise NotImplementedError
