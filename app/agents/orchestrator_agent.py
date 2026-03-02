"""PydanticAI Triage Orchestrator agent: agent-first composition via tools that delegate to Classification and Remediation agents."""

from __future__ import annotations

import logging
from typing import Any

import logfire
from pydantic_ai import Agent
from pydantic_ai.messages import ModelResponse, ToolReturnPart
from pydantic_ai.tools import RunContext

from app.agents._model import get_triage_model
from app.agents.classification_agent import (
    ClassificationAgentOutput,
    get_classification_agent,
)
from app.agents.remediation_agent import (
    RemediationAgentOutput,
    get_remediation_agent,
)
from app.contracts.triage import (
    ClassificationResult,
    NormalizedError,
    RemediationResult,
)

logger = logging.getLogger(__name__)

# Lazy singletons for delegate agents (avoid circular imports and allow test overrides)
_classification_agent: Agent[None, ClassificationAgentOutput] | None = None
_remediation_agent: Agent[None, RemediationAgentOutput] | None = None


def _get_classification_agent() -> Agent[None, ClassificationAgentOutput]:
    global _classification_agent
    if _classification_agent is None:
        _classification_agent = get_classification_agent()
    return _classification_agent


def _get_remediation_agent() -> Agent[None, RemediationAgentOutput]:
    global _remediation_agent
    if _remediation_agent is None:
        _remediation_agent = get_remediation_agent()
    return _remediation_agent


def _classify_tool(
    ctx: RunContext[None],
    message: str,
    item_index: int,
    source: str | None = None,
    tenant_id: str | None = None,
) -> dict:
    """Classify one error item (tool: delegates to Classification agent). Returns dict with item_index for ordering."""
    logfire.info(
        "agent tool call: classify",
        tool="classify",
        item_index=item_index,
        tenant_id=tenant_id,
        message_len=len(message),
    )
    with logfire.span("classify_tool", item_index=item_index, tenant_id=tenant_id):
        agent = _get_classification_agent()
        prompt = f"Error (tenant_id={tenant_id}): {message}"
        if source:
            prompt += f"\nSource: {source}"
        result = agent.run_sync(prompt)
        out = result.output
        out_dict = {
            "item_index": item_index,
            "classification": out.classification,
            "severity_score": out.severity_score,
            "handled": True,
        }
        logfire.info(
            "agent tool result: classify",
            tool="classify",
            item_index=item_index,
            classification=out.classification,
            severity_score=out.severity_score,
        )
        return out_dict


def _remediate_tool(
    ctx: RunContext[None],
    message: str,
    classification: str,
    severity_score: float,
    item_index: int,
    tenant_id: str | None = None,
) -> dict:
    """Suggest remediation for one item (tool: delegates to Remediation agent). Returns dict with item_index."""
    logfire.info(
        "agent tool call: remediate",
        tool="remediate",
        item_index=item_index,
        tenant_id=tenant_id,
        classification=classification,
        severity_score=severity_score,
    )
    with logfire.span("remediate_tool", item_index=item_index, tenant_id=tenant_id):
        agent = _get_remediation_agent()
        prompt = f"Classification: {classification}, severity: {severity_score}. Message: {message}. Tenant: {tenant_id}"
        result = agent.run_sync(prompt)
        out = result.output
        out_dict = {
            "item_index": item_index,
            "remediation_suggestion": out.remediation_suggestion,
            "used_fallback": False,
        }
        logfire.info(
            "agent tool result: remediate",
            tool="remediate",
            item_index=item_index,
            suggestion_len=len(out.remediation_suggestion),
        )
        return out_dict


ORCHESTRATOR_SYSTEM_PROMPT = (
    "You are a triage orchestrator. You have exactly two tools: 'classify' and 'remediate'. "
    "Do NOT call any other tool or use any other name. Only 'classify' and 'remediate' exist.\n"
    "For each error item you MUST call classify first (with message, item_index, optional source and tenant_id), "
    "then call remediate with that item's classification and severity_score (message, classification, severity_score, item_index, optional tenant_id). "
    "Process items in order by item_index (0, 1, 2, ...). "
    "After processing every item, respond with exactly this text and nothing else: Done."
)


def get_triage_orchestrator_agent() -> Agent[None, str]:
    """Orchestrator agent with classify and remediate tools (delegation to Classification and Remediation agents)."""
    model = get_triage_model()
    agent = Agent(
        model,
        output_type=str,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[_classify_tool, _remediate_tool],
        retries=5,
    )
    return agent


def _content_as_dict(part: ToolReturnPart) -> dict[str, Any]:
    """Extract tool return content as a dict for ordering and building results."""
    c = part.content
    if isinstance(c, dict):
        return c
    return {"item_index": -1}


def collect_tool_results_from_run(
    result: Any,
) -> tuple[list[ClassificationResult], list[RemediationResult]]:
    """Parse agent run result messages and return (classification_results, remediation_results) sorted by item_index."""
    classifications: list[tuple[int, ClassificationResult]] = []
    remediations: list[tuple[int, RemediationResult]] = []
    for message in result.all_messages():
        if not isinstance(message, ModelResponse):
            continue
        for part in message.parts:
            if not isinstance(part, ToolReturnPart):
                continue
            d = _content_as_dict(part)
            idx = d.get("item_index", -1)
            if part.tool_name == "classify":
                classifications.append(
                    (
                        idx,
                        ClassificationResult(
                            classification=d.get("classification", "unknown"),
                            severity_score=float(d.get("severity_score", 0.5)),
                            handled=True,
                            item_index=idx,
                        ),
                    )
                )
            elif part.tool_name == "remediate":
                remediations.append(
                    (
                        idx,
                        RemediationResult(
                            remediation_suggestion=d.get(
                                "remediation_suggestion", "Manual review required."
                            ),
                            item_index=idx,
                            used_fallback=bool(d.get("used_fallback", False)),
                        ),
                    )
                )
    classifications.sort(key=lambda x: x[0])
    remediations.sort(key=lambda x: x[0])
    return [c for _, c in classifications], [r for _, r in remediations]


def run_triage_via_agent(
    normalized_items: list[NormalizedError],
    tenant_id: str | None,
) -> tuple[list[ClassificationResult], list[RemediationResult], bool, bool]:
    """
    Agent-first path: run the orchestrator agent with the given items; collect tool results.
    Returns (classification_results, remediation_results, used_classification_fallback, used_remediation_fallback).
    On failure, returns fallback results (one per item) and sets fallback flags to True.
    """
    if not normalized_items:
        return [], [], False, False
    logger.info(
        "orchestrator agent run start item_count=%s tenant_id=%s", len(normalized_items), tenant_id
    )
    logfire.info(
        "orchestrator agent run start",
        item_count=len(normalized_items),
        tenant_id=tenant_id,
    )
    with logfire.span(
        "run_triage_via_agent", item_count=len(normalized_items), tenant_id=tenant_id
    ):
        agent = get_triage_orchestrator_agent()
        lines = [
            f"item_index={i}: message={norm.message!r}, source={norm.source!r}, tenant_id={norm.tenant_id!r}"
            for i, norm in enumerate(normalized_items)
        ]
        prompt = (
            "Process these items in order. Use ONLY the 'classify' and 'remediate' tools. "
            "For each item call classify then remediate with that item's results. When finished, reply: Done.\n\n"
            + "\n".join(lines)
        )
        try:
            result = agent.run_sync(prompt)
            cr, rem = collect_tool_results_from_run(result)
            if len(cr) != len(normalized_items) or len(rem) != len(normalized_items):
                logfire.warn(
                    "orchestrator agent fallback: tool call count mismatch",
                    expected=len(normalized_items),
                    classifications=len(cr),
                    remediations=len(rem),
                )
                return (
                    _fallback_results(normalized_items),
                    _fallback_remediations(normalized_items),
                    True,
                    True,
                )
            logfire.info(
                "orchestrator agent run complete",
                classification_count=len(cr),
                remediation_count=len(rem),
            )
            return cr, rem, False, False
        except Exception as e:
            logfire.exception("orchestrator agent run failed", error=str(e))
            return (
                _fallback_results(normalized_items),
                _fallback_remediations(normalized_items),
                True,
                True,
            )


def _fallback_results(normalized_items: list[NormalizedError]) -> list[ClassificationResult]:
    return [
        ClassificationResult(
            classification="unknown", severity_score=0.5, handled=True, item_index=norm.item_index
        )
        for norm in normalized_items
    ]


def _fallback_remediations(normalized_items: list[NormalizedError]) -> list[RemediationResult]:
    return [
        RemediationResult(
            remediation_suggestion="Manual review required.",
            item_index=norm.item_index,
            used_fallback=True,
        )
        for norm in normalized_items
    ]


def run_triage_via_agents_loop(
    normalized_items: list[NormalizedError],
    tenant_id: str | None,
) -> tuple[list[ClassificationResult], list[RemediationResult], bool, bool]:
    """
    Programmatic orchestration: for each item call Classification agent then Remediation agent.
    No orchestrator LLM — avoids model inventing tool names (e.g. process_errors, connection_timeout).
    Returns (classification_results, remediation_results, used_classification_fallback, used_remediation_fallback).
    """
    if not normalized_items:
        return [], [], False, False
    logger.info(
        "orchestrator agents loop start item_count=%s tenant_id=%s",
        len(normalized_items),
        tenant_id,
    )
    logfire.info(
        "orchestrator agents loop start",
        item_count=len(normalized_items),
        tenant_id=tenant_id,
    )
    classification_agent = _get_classification_agent()
    remediation_agent = _get_remediation_agent()
    cr_list: list[ClassificationResult] = []
    rem_list: list[RemediationResult] = []
    used_cf = False
    used_rf = False
    with logfire.span(
        "run_triage_via_agents_loop", item_count=len(normalized_items), tenant_id=tenant_id
    ):
        for norm in normalized_items:
            # Classify
            class_prompt = f"Error (tenant_id={tenant_id}): {norm.message}"
            if norm.source:
                class_prompt += f"\nSource: {norm.source}"
            try:
                logger.debug("classification agent call item_index=%s", norm.item_index)
                class_result = classification_agent.run_sync(class_prompt)
                logger.debug(
                    "classification agent result item_index=%s classification=%s",
                    norm.item_index,
                    class_result.output.classification,
                )
                cr_list.append(
                    ClassificationResult(
                        classification=class_result.output.classification,
                        severity_score=class_result.output.severity_score,
                        handled=True,
                        item_index=norm.item_index,
                    )
                )
            except Exception as e:
                logfire.warn(
                    "classification agent failed for item", item_index=norm.item_index, error=str(e)
                )
                used_cf = True
                cr_list.append(
                    ClassificationResult(
                        classification="unknown",
                        severity_score=0.5,
                        handled=True,
                        item_index=norm.item_index,
                    )
                )
                rem_list.append(
                    RemediationResult(
                        remediation_suggestion="Manual review required.",
                        item_index=norm.item_index,
                        used_fallback=True,
                    )
                )
                used_rf = True
                continue
            # Remediate
            rem_prompt = (
                f"Classification: {cr_list[-1].classification}, severity: {cr_list[-1].severity_score}. "
                f"Message: {norm.message}. Tenant: {tenant_id}"
            )
            try:
                logger.debug("remediation agent call item_index=%s", norm.item_index)
                rem_result = remediation_agent.run_sync(rem_prompt)
                logger.debug("remediation agent result item_index=%s", norm.item_index)
                rem_list.append(
                    RemediationResult(
                        remediation_suggestion=rem_result.output.remediation_suggestion,
                        item_index=norm.item_index,
                        used_fallback=False,
                    )
                )
            except Exception as e:
                logfire.warn(
                    "remediation agent failed for item", item_index=norm.item_index, error=str(e)
                )
                used_rf = True
                rem_list.append(
                    RemediationResult(
                        remediation_suggestion="Manual review required.",
                        item_index=norm.item_index,
                        used_fallback=True,
                    )
                )
        logfire.info(
            "orchestrator agents loop complete",
            classification_count=len(cr_list),
            remediation_count=len(rem_list),
        )
    return cr_list, rem_list, used_cf, used_rf
