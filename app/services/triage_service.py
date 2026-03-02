"""Triage service: agent-first composition. Planner → runner (orchestrator agent or stub) → Executor."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable

import logfire

from app.agents.orchestrator_agent import run_triage_via_agent, run_triage_via_agents_loop
from app.contracts.triage import (
    ClassificationResult,
    PlanResult,
    RemediationResult,
    TriageRequest,
    TriageResponse,
)
from app.executor.triage_executor import TriageExecutor
from app.planner.triage_planner import TriagePlanner

logger = logging.getLogger(__name__)

# Runner: (plan, tenant_id) -> (classification_results, remediation_results, used_cf, used_rf)
TriageRunner = Callable[
    [PlanResult, str | None],
    tuple[list[ClassificationResult], list[RemediationResult], bool, bool],
]


def _use_orchestrator_agent() -> bool:
    """Use orchestrator agent (LLM chooses tools) when USE_ORCHESTRATOR_AGENT=1 or LITELLM_MODEL is anthropic/* (e.g. Claude)."""
    if os.environ.get("USE_ORCHESTRATOR_AGENT", "").lower() in ("1", "true", "yes"):
        return True
    model = os.environ.get("LITELLM_MODEL", "")
    return model.startswith("anthropic/")


def _default_runner(
    plan: PlanResult, tenant_id: str | None
) -> tuple[list[ClassificationResult], list[RemediationResult], bool, bool]:
    """Use orchestrator agent (tool choice) when Claude/anthropic or USE_ORCHESTRATOR_AGENT=1; else programmatic loop."""
    if _use_orchestrator_agent():
        logger.info("triage runner: orchestrator agent (LLM chooses classify/remediate tools)")
        return run_triage_via_agent(plan.normalized_items, tenant_id)
    logger.info("triage runner: programmatic agents loop (no orchestrator LLM)")
    return run_triage_via_agents_loop(plan.normalized_items, tenant_id)


class TriageService:
    """
    Entrypoint for batch triage. Default: Planner → runner (programmatic Classification+Remediation agents loop) → Executor.
    Optional runner for tests/promptfoo (stub) so no LLM is called.
    """

    def __init__(
        self,
        runner: TriageRunner | None = None,
        planner: TriagePlanner | None = None,
        executor: TriageExecutor | None = None,
    ):
        self._runner: TriageRunner = runner or _default_runner
        self._planner = planner or TriagePlanner()
        self._executor = executor or TriageExecutor()

    def run_triage(self, request: TriageRequest) -> TriageResponse:
        """Run the triage pipeline and return the validated response."""
        logger.info(
            "triage run_triage start item_count=%s tenant_id=%s",
            len(request.items),
            request.tenant_id,
        )
        with logfire.span("triage_service.run_triage", tenant_id=request.tenant_id):
            plan = self._planner.plan(request)
            logger.debug("triage plan normalized_count=%s", len(plan.normalized_items))
            logfire.info(
                "triage plan",
                normalized_count=len(plan.normalized_items),
                tenant_id=request.tenant_id,
            )
            if not plan.normalized_items:
                logfire.info("triage skipped", reason="no normalized items")
                return self._executor.execute(
                    [],
                    [],
                    tenant_id=request.tenant_id,
                    used_classification_fallback=False,
                    used_remediation_fallback=False,
                )
            cr, rem, used_cf, used_rf = self._runner(plan, request.tenant_id)
            logfire.info(
                "triage runner complete",
                classification_count=len(cr),
                remediation_count=len(rem),
                used_classification_fallback=used_cf,
                used_remediation_fallback=used_rf,
            )
            return self._executor.execute(
                classification_results=cr,
                remediation_results=rem,
                tenant_id=request.tenant_id,
                used_classification_fallback=used_cf,
                used_remediation_fallback=used_rf,
            )
