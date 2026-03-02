"""API: POST /v1/triage with synthetic batch; tenant_id; validation."""

from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures import synthetic_request_dict


client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_triage_post_success_with_tenant_id() -> None:
    body = synthetic_request_dict()
    r = client.post("/v1/triage", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["tenant_id"] == "tenant_001"
    assert "results" in data
    assert len(data["results"]) == len(body["items"])
    for res in data["results"]:
        assert "classification" in res
        assert "severity_score" in res
        assert "remediation_suggestion" in res


def test_triage_post_empty_items_422() -> None:
    r = client.post("/v1/triage", json={"schema_version": "1.0", "tenant_id": "t1", "items": []})
    assert r.status_code == 422


def test_triage_post_tenant_id_propagated_in_response() -> None:
    body = {"tenant_id": "t42", "items": [{"message": "timeout", "code": 504}]}
    r = client.post("/v1/triage", json=body)
    assert r.status_code == 200
    assert r.json()["tenant_id"] == "t42"
