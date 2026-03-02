"""Synthetic error payloads for demo and tests. Multiple shapes (inconsistent schemas)."""

from app.contracts.triage import TriageRequest, TriageRequestItem

# Different "shapes" to simulate semi-structured ingest
SYNTHETIC_ITEMS = [
    # Shape 1: message + code
    TriageRequestItem(
        raw_payload={"message": "Connection timed out after 30s", "code": 504},
        message="Connection timed out after 30s",
    ),
    # Shape 2: error_detail + stack
    TriageRequestItem(
        raw_payload={
            "error_detail": "404 Not Found",
            "path": "/api/orders/xyz",
            "stack": "Traceback ...",
        },
    ),
    # Shape 3: minimal
    TriageRequestItem(raw_payload={"msg": "rate limit exceeded"}, message="rate limit exceeded"),
]

SYNTHETIC_REQUEST = TriageRequest(
    schema_version="1.0",
    tenant_id="tenant_001",
    items=SYNTHETIC_ITEMS,
)


def synthetic_request_dict() -> dict:
    """JSON-serializable request for TestClient."""
    return {
        "schema_version": "1.0",
        "tenant_id": "tenant_001",
        "items": [
            {"message": "Connection timed out after 30s", "code": 504},
            {"error_detail": "404 Not Found", "path": "/api/orders/xyz"},
            {"msg": "rate limit exceeded"},
        ],
    }
