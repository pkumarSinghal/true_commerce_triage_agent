"""POST /v1/triage: batch triage endpoint. Tenant-aware."""

from fastapi import APIRouter, HTTPException
from app.contracts.triage import TriageRequest, TriageResponse
from app.orchestrator.triage_orchestrator import TriageOrchestrator

router = APIRouter(prefix="/v1", tags=["triage"])
_orchestrator: TriageOrchestrator | None = None


def get_orchestrator() -> TriageOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TriageOrchestrator()
    return _orchestrator


@router.post("/triage", response_model=TriageResponse)
def post_triage(request: TriageRequest) -> TriageResponse:
    """Accept batch of semi-structured error items; return classification, severity, remediation per item."""
    if not request.items:
        raise HTTPException(status_code=422, detail="items must not be empty")
    orchestrator = get_orchestrator()
    return orchestrator.run_triage(request)
