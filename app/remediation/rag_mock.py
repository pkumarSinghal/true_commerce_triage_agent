"""Mock RAG: in-memory doc store for tests; tenant-aware placeholder for production vector store."""

from app.contracts.triage import NormalizedError


# Default mock docs (tenant-agnostic for MVP)
DEFAULT_DOCS = [
    "Timeout errors: check network and retry with backoff.",
    "Connection refused: verify service is running and port is open.",
    "404 Not Found: validate resource ID and path.",
    "500 Server Error: check server logs and retry after mitigation.",
]


class RAGMock:
    """In-memory RAG: returns fixed docs or tenant-keyed docs. Production swaps for vector store."""

    def __init__(self, docs: list[str] | None = None, tenant_docs: dict[str, list[str]] | None = None):
        self.docs = docs or DEFAULT_DOCS
        self.tenant_docs = tenant_docs or {}

    def retrieve(self, query: str, tenant_id: str | None = None, top_k: int = 3) -> list[str]:
        """Return relevant docs. Mock: returns tenant-specific if any, else default."""
        if tenant_id and tenant_id in self.tenant_docs:
            return self.tenant_docs[tenant_id][:top_k]
        return self.docs[:top_k]

    def retrieve_for_context(self, normalized: NormalizedError, top_k: int = 3) -> str:
        """Return concatenated context string for prompt."""
        docs = self.retrieve(normalized.message, normalized.tenant_id, top_k=top_k)
        return "\n".join(docs) if docs else ""
