"""Executor: aggregates ClassificationResult + RemediationResult per item into TriageResponse."""

from app.contracts.triage import (
    ClassificationResult,
    RemediationResult,
    TriageResponse,
    TriageResult,
    SCHEMA_VERSION,
)


class TriageExecutor:
    """Builds validated TriageResponse from per-item classification and remediation. No LLM."""

    def execute(
        self,
        classification_results: list[ClassificationResult],
        remediation_results: list[RemediationResult],
        tenant_id: str | None = None,
        used_classification_fallback: bool = False,
        used_remediation_fallback: bool = False,
    ) -> TriageResponse:
        """Match by item_index and produce TriageResult list; set tenant_id and fallback flags."""
        by_idx = {r.item_index: r for r in remediation_results}
        results: list[TriageResult] = []
        for c in classification_results:
            rem = by_idx.get(c.item_index)
            suggestion = rem.remediation_suggestion if rem else "Manual review required."
            results.append(
                TriageResult(
                    classification=c.classification,
                    severity_score=c.severity_score,
                    remediation_suggestion=suggestion,
                    item_id=None,
                    raw_item_index=c.item_index,
                )
            )
        return TriageResponse(
            schema_version=SCHEMA_VERSION,
            tenant_id=tenant_id,
            results=results,
            used_classification_fallback=used_classification_fallback,
            used_remediation_fallback=used_remediation_fallback,
        )
