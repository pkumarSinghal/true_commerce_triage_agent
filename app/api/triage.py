"""POST /v1/triage: batch triage endpoint. Tenant-aware."""

import json
import logging

import logfire
from fastapi import APIRouter, HTTPException

from app.contracts.triage import TriageRequest, TriageResponse
from app.services.triage_service import TriageService

router = APIRouter(prefix="/v1", tags=["triage"])
logger = logging.getLogger(__name__)
_triage_service: TriageService | None = None

_MAX_LOG_STR = 500


def _trunc(s: str | None, max_len: int = _MAX_LOG_STR) -> str | None:
    if s is None:
        return None
    return s if len(s) <= max_len else s[:max_len] + "..."


def get_triage_service() -> TriageService:
    global _triage_service
    if _triage_service is None:
        _triage_service = TriageService()
    return _triage_service


@router.post("/triage", response_model=TriageResponse)
def post_triage(request: TriageRequest) -> TriageResponse:
    """Accept batch of semi-structured error items; return classification, severity, remediation per item."""
    if not request.items:
        raise HTTPException(status_code=422, detail="items must not be empty")
    item_count = len(request.items)
    request_log = {
        "schema_version": request.schema_version,
        "tenant_id": request.tenant_id,
        "item_count": item_count,
        "items": [
            {
                "message": _trunc(getattr(it, "message", None)),
                "source": it.source,
                "timestamp": it.timestamp,
                "raw_payload_keys": list(it.raw_payload.keys()) if it.raw_payload else [],
            }
            for it in request.items
        ],
    }
    logfire.info("post_triage request", request=request_log)
    logger.info("triage request: %s", json.dumps(request_log, default=str))
    with logfire.span("triage_request", item_count=item_count, tenant_id=request.tenant_id):
        service = get_triage_service()
        response = service.run_triage(request)
    response_log = {
        "schema_version": response.schema_version,
        "tenant_id": response.tenant_id,
        "result_count": len(response.results),
        "used_classification_fallback": response.used_classification_fallback,
        "used_remediation_fallback": response.used_remediation_fallback,
        "results": [
            {
                "classification": r.classification,
                "severity_score": r.severity_score,
                "remediation_suggestion": _trunc(r.remediation_suggestion),
                "raw_item_index": r.raw_item_index,
            }
            for r in response.results
        ],
    }
    logfire.info("post_triage response", response=response_log)
    logger.info("triage response: %s", json.dumps(response_log, default=str))
    return response
