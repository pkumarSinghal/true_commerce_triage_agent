"""Orchestrator: consumes TriageRequest, propagates tenant_id, runs pipeline to TriageResponse."""

from app.contracts.triage import (
    ClassificationResult,
    PlanResult,
    RemediationResult,
    TriageRequest,
    TriageResponse,
)
from app.planner.triage_planner import TriagePlanner
from app.classifier.rule_based import RuleBasedClassifier
from app.classifier.classification_llm import ClassificationLLMFallback
from app.remediation.remediation_llm import RemediationLLM
from app.executor.triage_executor import TriageExecutor
from app.core.circuit_breaker import CircuitBreaker


class TriageOrchestrator:
    """Deterministic orchestration: Planner → Classifier (→ Classification LLM if unhandled) → Remediation LLM → Executor."""

    def __init__(
        self,
        planner: TriagePlanner | None = None,
        classifier: RuleBasedClassifier | None = None,
        classification_llm: ClassificationLLMFallback | None = None,
        remediation_llm: RemediationLLM | None = None,
        executor: TriageExecutor | None = None,
        classification_breaker: CircuitBreaker | None = None,
        remediation_breaker: CircuitBreaker | None = None,
    ):
        self.planner = planner or TriagePlanner()
        self.classifier = classifier or RuleBasedClassifier()
        self.classification_llm = classification_llm or ClassificationLLMFallback(
            circuit_breaker=classification_breaker or CircuitBreaker()
        )
        self.remediation_llm = remediation_llm or RemediationLLM(
            circuit_breaker=remediation_breaker or CircuitBreaker()
        )
        self.executor = executor or TriageExecutor()

    def run_triage(self, request: TriageRequest) -> TriageResponse:
        """Execute pipeline; propagate tenant_id; track fallback usage."""
        plan = self.planner.plan(request)
        cr, rem, used_cf, used_rf = self.run_triage_from_plan(plan, request.tenant_id)
        return self.executor.execute(
            classification_results=cr,
            remediation_results=rem,
            tenant_id=request.tenant_id,
            used_classification_fallback=used_cf,
            used_remediation_fallback=used_rf,
        )

    def run_triage_from_plan(
        self, plan: PlanResult, tenant_id: str | None
    ) -> tuple[list[ClassificationResult], list[RemediationResult], bool, bool]:
        """Run classifier + classification LLM + remediation LLM over plan; return (cr, rem, used_cf, used_rf). Used as stub runner for tests and promptfoo."""
        classification_results: list[ClassificationResult] = []
        remediation_results: list[RemediationResult] = []
        used_classification_fallback = False
        used_remediation_fallback = False
        for norm in plan.normalized_items:
            cr = self.classifier.classify(norm)
            if not cr.handled:
                cr = self.classification_llm.classify(norm)
                used_classification_fallback = True
            classification_results.append(cr)
            rem = self.remediation_llm.suggest(norm, cr)
            if rem.used_fallback:
                used_remediation_fallback = True
            remediation_results.append(rem)
        return (
            classification_results,
            remediation_results,
            used_classification_fallback,
            used_remediation_fallback,
        )
