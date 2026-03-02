"""Pytest fixtures: inject stub RemediationLLM so API tests run offline (no LLM)."""

import pytest
from app.orchestrator.triage_orchestrator import TriageOrchestrator
from tests.stubs import StubRemediationLLM


@pytest.fixture
def stub_orchestrator() -> TriageOrchestrator:
    return TriageOrchestrator(remediation_llm=StubRemediationLLM())


@pytest.fixture(autouse=True)
def override_orchestrator(stub_orchestrator: TriageOrchestrator) -> None:
    """Inject stub orchestrator into API so tests don't call real LLM."""
    import app.api.triage as triage_api
    original = triage_api.get_orchestrator
    triage_api.get_orchestrator = lambda: stub_orchestrator
    yield
    triage_api.get_orchestrator = original
