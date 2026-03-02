"""PydanticAI agents: Classification, Remediation, and orchestrator loop (offline with TestModel)."""

import pytest

from pydantic_ai import models
from pydantic_ai.models.test import TestModel

from app.agents.classification_agent import ClassificationAgentOutput, get_classification_agent
from app.agents.remediation_agent import RemediationAgentOutput, get_remediation_agent
from app.agents.orchestrator_agent import (
    _get_classification_agent,
    _get_remediation_agent,
    collect_tool_results_from_run,
    get_triage_orchestrator_agent,
    run_triage_via_agent,
    run_triage_via_agents_loop,
)
from app.contracts.triage import NormalizedError

# Block real LLM requests in tests
models.ALLOW_MODEL_REQUESTS = False


def test_classification_agent_returns_structured_output() -> None:
    """Classification agent with TestModel returns valid ClassificationAgentOutput."""
    agent = get_classification_agent()
    with agent.override(model=TestModel()):
        result = agent.run_sync("Connection timed out after 30s")
    assert result.output is not None
    assert isinstance(result.output, ClassificationAgentOutput)
    assert isinstance(result.output.classification, str)
    assert len(result.output.classification) > 0
    assert 0.0 <= result.output.severity_score <= 1.0


def test_remediation_agent_returns_structured_output() -> None:
    """Remediation agent with TestModel returns valid RemediationAgentOutput."""
    agent = get_remediation_agent()
    with agent.override(model=TestModel()):
        result = agent.run_sync(
            "Classification: timeout, severity: 0.8. Message: Connection timed out. Tenant: t1"
        )
    assert result.output is not None
    assert isinstance(result.output, RemediationAgentOutput)
    assert isinstance(result.output.remediation_suggestion, str)
    assert len(result.output.remediation_suggestion) > 0


def test_run_triage_via_agents_loop_with_test_model() -> None:
    """Programmatic agents loop with TestModel returns one classification and remediation per item."""
    items = [
        NormalizedError(message="timeout error", item_index=0),
        NormalizedError(message="404 not found", source="api", item_index=1),
    ]
    c_agent = _get_classification_agent()
    r_agent = _get_remediation_agent()
    with c_agent.override(model=TestModel()), r_agent.override(model=TestModel()):
        cr, rem, used_cf, used_rf = run_triage_via_agents_loop(items, "tenant_001")
    assert len(cr) == 2
    assert len(rem) == 2
    assert used_cf is False
    assert used_rf is False
    for i, c in enumerate(cr):
        assert c.item_index == i
        assert isinstance(c.classification, str)
        assert 0.0 <= c.severity_score <= 1.0
    for i, r in enumerate(rem):
        assert r.item_index == i
        assert isinstance(r.remediation_suggestion, str)


def test_run_triage_via_agents_loop_empty_items() -> None:
    """Agents loop with no items returns empty lists and no fallback."""
    cr, rem, used_cf, used_rf = run_triage_via_agents_loop([], "t1")
    assert cr == []
    assert rem == []
    assert used_cf is False
    assert used_rf is False


def test_run_triage_via_agent_orchestrator_with_test_model() -> None:
    """Orchestrator agent (LLM chooses tools) with TestModel; delegate agents also use TestModel."""
    items = [NormalizedError(message="timeout", item_index=0)]
    c_agent = _get_classification_agent()
    r_agent = _get_remediation_agent()
    o_agent = get_triage_orchestrator_agent()
    with (
        c_agent.override(model=TestModel()),
        r_agent.override(model=TestModel()),
        o_agent.override(model=TestModel()),
    ):
        cr, rem, used_cf, used_rf = run_triage_via_agent(items, "tenant_001")
    assert len(cr) == 1
    assert len(rem) == 1
    assert isinstance(cr[0].classification, str)
    assert 0.0 <= cr[0].severity_score <= 1.0
    assert isinstance(rem[0].remediation_suggestion, str)


def test_collect_tool_results_from_run() -> None:
    """collect_tool_results_from_run parses tool return parts into classification and remediation lists."""
    from pydantic_ai.messages import ModelResponse, ToolReturnPart

    # Build a minimal fake result with all_messages that contain ToolReturnPart
    class FakeResult:
        def all_messages(self):
            return [
                ModelResponse(
                    parts=[
                        ToolReturnPart(
                            tool_name="classify",
                            content={"item_index": 0, "classification": "timeout", "severity_score": 0.7},
                        ),
                        ToolReturnPart(
                            tool_name="remediate",
                            content={"item_index": 0, "remediation_suggestion": "Retry.", "used_fallback": False},
                        ),
                        ToolReturnPart(
                            tool_name="classify",
                            content={"item_index": 1, "classification": "not_found", "severity_score": 0.4},
                        ),
                        ToolReturnPart(
                            tool_name="remediate",
                            content={"item_index": 1, "remediation_suggestion": "Check path.", "used_fallback": False},
                        ),
                    ],
                )
            ]

    result = FakeResult()
    cr, rem = collect_tool_results_from_run(result)
    assert len(cr) == 2
    assert len(rem) == 2
    assert cr[0].classification == "timeout"
    assert cr[0].severity_score == 0.7
    assert cr[1].classification == "not_found"
    assert rem[0].remediation_suggestion == "Retry."
    assert rem[1].remediation_suggestion == "Check path."
