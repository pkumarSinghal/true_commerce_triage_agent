"""Synthetic error payloads for demo and tests. Multiple shapes (inconsistent schemas)."""

from app.contracts.triage import TriageRequest, TriageRequestItem

# 10 different shapes for semi-structured ingest (used in two batches of 4-5)
SYNTHETIC_ITEMS = [
    TriageRequestItem(
        raw_payload={"message": "Connection timed out after 30s", "code": 504},
        message="Connection timed out after 30s",
    ),
    TriageRequestItem(
        raw_payload={
            "error_detail": "404 Not Found",
            "path": "/api/orders/xyz",
            "stack": "Traceback ...",
        },
    ),
    TriageRequestItem(raw_payload={"msg": "rate limit exceeded"}, message="rate limit exceeded"),
    TriageRequestItem(
        raw_payload={"message": "Internal Server Error", "code": 500, "request_id": "req-1"},
        message="Internal Server Error",
    ),
    TriageRequestItem(
        raw_payload={"error": "Unauthorized", "code": 401, "realm": "api"},
        message="Unauthorized",
    ),
    TriageRequestItem(
        raw_payload={
            "message": "Validation failed",
            "code": 422,
            "errors": [{"field": "amount", "detail": "must be positive"}],
        },
        message="Validation failed",
    ),
    TriageRequestItem(
        raw_payload={"message": "Database connection refused", "db": "orders"},
        message="Database connection refused",
    ),
    TriageRequestItem(
        raw_payload={"message": "Network unreachable", "host": "api.upstream.com"},
        message="Network unreachable",
    ),
    TriageRequestItem(raw_payload={"err": "partial payload"}, message="partial payload"),
    TriageRequestItem(
        raw_payload={"message": "Service unavailable", "code": 503, "source": "gateway", "timestamp": "2025-01-15T12:00:00Z"},
        message="Service unavailable",
    ),
]

# Batch 1: first 5 items. Batch 2: next 5 items.
SYNTHETIC_BATCH1_ITEMS = SYNTHETIC_ITEMS[:5]
SYNTHETIC_BATCH2_ITEMS = SYNTHETIC_ITEMS[5:10]

SYNTHETIC_REQUEST = TriageRequest(
    schema_version="1.0",
    tenant_id="tenant_001",
    items=SYNTHETIC_ITEMS,
)

SYNTHETIC_BATCH1_REQUEST = TriageRequest(
    schema_version="1.0",
    tenant_id="tenant_001",
    items=SYNTHETIC_BATCH1_ITEMS,
)

SYNTHETIC_BATCH2_REQUEST = TriageRequest(
    schema_version="1.0",
    tenant_id="tenant_001",
    items=SYNTHETIC_BATCH2_ITEMS,
)


def _items_to_json_items(items: list[TriageRequestItem]) -> list[dict]:
    """Convert TriageRequestItems to JSON-serializable item dicts (raw_payload shape)."""
    out = []
    for it in items:
        d = dict(it.raw_payload)
        if it.message is not None and "message" not in d:
            d["message"] = it.message
        out.append(d)
    return out


def synthetic_request_dict() -> dict:
    """JSON-serializable request for TestClient (original 3-item set for backward compat)."""
    return {
        "schema_version": "1.0",
        "tenant_id": "tenant_001",
        "items": [
            {"message": "Connection timed out after 30s", "code": 504},
            {"error_detail": "404 Not Found", "path": "/api/orders/xyz"},
            {"msg": "rate limit exceeded"},
        ],
    }


def synthetic_batch1_dict() -> dict:
    """JSON-serializable batch 1 (5 items) for live API tests and promptfoo."""
    return {
        "schema_version": "1.0",
        "tenant_id": "tenant_001",
        "items": _items_to_json_items(SYNTHETIC_BATCH1_ITEMS),
    }


def synthetic_batch2_dict() -> dict:
    """JSON-serializable batch 2 (5 items) for live API tests and promptfoo."""
    return {
        "schema_version": "1.0",
        "tenant_id": "tenant_001",
        "items": _items_to_json_items(SYNTHETIC_BATCH2_ITEMS),
    }
