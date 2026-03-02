"""PydanticAI Remediation agent: structured output for remediation suggestion (used as tool by orchestrator or by LLM layer)."""

from pydantic import BaseModel, Field

from pydantic_ai import Agent

from app.agents._model import get_triage_model

REMEDIATION_PROMPT_VERSION = "1.0"


class RemediationAgentOutput(BaseModel):
    """What the remediation agent returns; caller adds item_index and used_fallback."""

    remediation_suggestion: str = Field(
        description="Short, actionable remediation suggestion (one or two sentences)"
    )


def get_remediation_agent() -> Agent[None, RemediationAgentOutput]:
    """Return the Remediation PydanticAI agent (structured output)."""
    return Agent(
        get_triage_model(),
        output_type=RemediationAgentOutput,
        system_prompt=(
            "You are a remediation advisor. Given an error classification, severity, and message, "
            "output a short, actionable remediation suggestion (one or two sentences). "
            "Use any provided documentation context if relevant."
        ),
    )
