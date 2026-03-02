"""Planner: normalize batch, include tenant_id."""

from app.contracts.triage import TriageRequest, TriageRequestItem
from app.planner.triage_planner import TriagePlanner


def test_plan_normalizes_items_and_includes_tenant_id() -> None:
    request = TriageRequest(
        tenant_id="t1",
        items=[
            TriageRequestItem(raw_payload={"message": "timeout"}, message="timeout"),
            TriageRequestItem(raw_payload={}, message="err"),
        ],
    )
    planner = TriagePlanner()
    result = planner.plan(request)
    assert len(result.normalized_items) == 2
    assert result.normalized_items[0].message == "timeout"
    assert result.normalized_items[0].tenant_id == "t1"
    assert result.normalized_items[0].item_index == 0
    assert result.normalized_items[1].item_index == 1


def test_plan_extracts_message_from_payload_when_no_top_level_message() -> None:
    request = TriageRequest(
        items=[
            TriageRequestItem(raw_payload={"error_detail": "404", "path": "/x"}),
        ],
    )
    planner = TriagePlanner()
    result = planner.plan(request)
    assert "404" in result.normalized_items[0].message or ""
