"""Orchestrator: full pipeline with mocks; tenant_id propagated; fallback flags."""

from app.contracts.triage import TriageRequest, TriageRequestItem, TriageResponse
from app.classifier.rule_based import RuleBasedClassifier
from app.orchestrator.triage_orchestrator import TriageOrchestrator
from tests.stubs import StubClassificationLLM, StubRemediationLLM


def test_orchestrator_returns_triage_response_with_tenant_id() -> None:
    request = TriageRequest(
        tenant_id="tenant_42",
        items=[
            TriageRequestItem(raw_payload={"message": "timeout"}, message="timeout"),
        ],
    )
    orch = TriageOrchestrator(
        classifier=RuleBasedClassifier(),
        remediation_llm=StubRemediationLLM(),
    )
    # Use RuleBasedClassifier so we don't need LLM; stub remediation
    response = orch.run_triage(request)
    assert isinstance(response, TriageResponse)
    assert response.tenant_id == "tenant_42"
    assert len(response.results) == 1
    assert response.results[0].classification == "timeout"
    assert response.results[0].remediation_suggestion == "Check logs and retry."


def test_orchestrator_propagates_tenant_id_when_none() -> None:
    request = TriageRequest(
        items=[TriageRequestItem(raw_payload={"message": "500 error"}, message="500 error")],
    )
    orch = TriageOrchestrator(
        classifier=RuleBasedClassifier(),
        remediation_llm=StubRemediationLLM(),
    )
    response = orch.run_triage(request)
    assert response.tenant_id is None
    assert len(response.results) == 1


def test_orchestrator_classification_fallback_path_uses_stub_llm() -> None:
    """When rule-based classifier returns handled=False, orchestrator uses Classification LLM; stub returns fixed result."""
    # Message that does not match any RuleBasedClassifier pattern -> handled=False
    request = TriageRequest(
        tenant_id="tenant_99",
        items=[
            TriageRequestItem(
                raw_payload={"message": "obscure widget failure xyz"},
                message="obscure widget failure xyz",
            ),
        ],
    )
    orch = TriageOrchestrator(
        classifier=RuleBasedClassifier(),
        classification_llm=StubClassificationLLM(),
        remediation_llm=StubRemediationLLM(),
    )
    response = orch.run_triage(request)
    assert response.used_classification_fallback is True
    assert len(response.results) == 1
    assert response.results[0].classification == "unknown"
    assert response.results[0].severity_score == 0.5
    assert response.results[0].remediation_suggestion == "Check logs and retry."
