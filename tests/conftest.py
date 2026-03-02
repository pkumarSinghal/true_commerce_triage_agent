"""Pytest fixtures: inject stub runner via TriageService so API tests run offline (no LLM)."""

import asyncio
import os

import pytest

# Suppress logfire warning when tests log without logfire.configure()
os.environ.setdefault("LOGFIRE_IGNORE_NO_CONFIG", "1")

# Ensure an event loop exists for sync tests that call agent.run_sync() (avoids DeprecationWarning)
@pytest.fixture(scope="session", autouse=True)
def _event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


from app.orchestrator.triage_orchestrator import TriageOrchestrator
from app.services.triage_service import TriageService
from tests.stubs import StubRemediationLLM


@pytest.fixture
def stub_orchestrator() -> TriageOrchestrator:
    return TriageOrchestrator(remediation_llm=StubRemediationLLM())


@pytest.fixture(autouse=True)
def override_triage_service(stub_orchestrator: TriageOrchestrator) -> None:
    """Inject stub runner into API via TriageService so tests don't call real LLM."""
    import app.api.triage as triage_api
    stub_runner = stub_orchestrator.run_triage_from_plan
    stub_service = TriageService(runner=stub_runner)
    original = triage_api.get_triage_service
    triage_api.get_triage_service = lambda: stub_service
    yield
    triage_api.get_triage_service = original
