"""Triage request/response and internal pipeline contracts. Tenant-aware."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0"


class TriageRequestItem(BaseModel):
    """Single error item; flexible schema for semi-structured payloads."""

    model_config = ConfigDict(extra="allow")

    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Raw error payload")
    message: str | None = None
    source: str | None = None
    timestamp: str | None = None

    @model_validator(mode="after")
    def merge_extra_into_raw_payload(self) -> "TriageRequestItem":
        """Copy extra keys (e.g. from JSON) into raw_payload for flexible ingest."""
        extra = getattr(self, "__pydantic_extra__", None) or {}
        if extra:
            self.raw_payload = {**self.raw_payload, **extra}
        return self

    def get_payload_for_context(self) -> dict[str, Any]:
        """Merge raw_payload with any top-level message/source/timestamp for context."""
        out = dict(self.raw_payload)
        if self.message is not None:
            out["message"] = self.message
        if self.source is not None:
            out["source"] = self.source
        if self.timestamp is not None:
            out["timestamp"] = self.timestamp
        return out


class TriageRequest(BaseModel):
    """Batch triage request. Tenant-aware."""

    schema_version: str = Field(default=SCHEMA_VERSION)
    tenant_id: str | None = None
    items: list[TriageRequestItem] = Field(default_factory=list, max_length=100)


class TriageResult(BaseModel):
    """Single triage result for one item."""

    classification: str
    severity_score: float = Field(ge=0.0, le=1.0)
    remediation_suggestion: str
    item_id: str | None = None
    raw_item_index: int | None = None


class TriageResponse(BaseModel):
    """Batch triage response. Tenant-aware; fallback flags for observability."""

    schema_version: str = Field(default=SCHEMA_VERSION)
    tenant_id: str | None = None
    results: list[TriageResult] = Field(default_factory=list)
    used_classification_fallback: bool = False
    used_remediation_fallback: bool = False


# --- Internal pipeline contracts ---


class NormalizedError(BaseModel):
    """Normalized error context after Planner. Tenant-aware."""

    message: str
    source: str | None = None
    timestamp: str | None = None
    tenant_id: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    item_index: int = 0


class PlanResult(BaseModel):
    """Output of Planner: normalized items ready for Classifier."""

    schema_version: str = Field(default=SCHEMA_VERSION)
    normalized_items: list[NormalizedError] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    """Output of Classifier (or Classification LLM fallback)."""

    classification: str
    severity_score: float = Field(ge=0.0, le=1.0)
    handled: bool = True
    item_index: int = 0


class RemediationResult(BaseModel):
    """Output of Remediation LLM."""

    remediation_suggestion: str
    item_index: int = 0
    used_fallback: bool = False
