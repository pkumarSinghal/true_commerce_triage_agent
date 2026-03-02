"""Planner: normalize batch items into NormalizedError list. Tenant-aware; no LLM."""

import logging

from app.contracts.triage import (
    PlanResult,
    NormalizedError,
    TriageRequest,
    SCHEMA_VERSION,
)

logger = logging.getLogger(__name__)


class TriagePlanner:
    """Normalizes request items into a list of NormalizedError with tenant_id."""

    def plan(self, request: TriageRequest) -> PlanResult:
        """Produce PlanResult from TriageRequest. Include tenant_id in each normalized item."""
        normalized: list[NormalizedError] = []
        for i, item in enumerate(request.items):
            payload = item.get_payload_for_context()
            message = item.message or payload.get("message") or str(payload)[:500]
            source = item.source or payload.get("source") or payload.get("code")
            if source is not None:
                source = str(source)
            timestamp = item.timestamp or payload.get("timestamp")
            if timestamp is not None:
                timestamp = str(timestamp)
            normalized.append(
                NormalizedError(
                    message=message,
                    source=source,
                    timestamp=timestamp,
                    tenant_id=request.tenant_id,
                    raw_payload=payload,
                    item_index=i,
                )
            )
        result = PlanResult(schema_version=SCHEMA_VERSION, normalized_items=normalized)
        logger.debug(
            "planner plan item_count=%s normalized_count=%s", len(request.items), len(normalized)
        )
        return result
