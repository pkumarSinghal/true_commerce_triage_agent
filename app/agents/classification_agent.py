"""PydanticAI Classification agent: structured output for error classification (used as tool by orchestrator or by fallback)."""

from pydantic import BaseModel, Field

from pydantic_ai import Agent

from app.agents._model import get_triage_model

# Output shape from the LLM; item_index and handled are set by the caller
CLASSIFICATION_PROMPT_VERSION = "1.0"


class ClassificationAgentOutput(BaseModel):
    """What the classification agent returns; caller adds item_index and handled."""

    classification: str = Field(description="One word or snake_case label for the error type")
    severity_score: float = Field(ge=0.0, le=1.0, description="Severity from 0.0 to 1.0")


def get_classification_agent() -> Agent[None, ClassificationAgentOutput]:
    """Return the Classification PydanticAI agent (structured output)."""
    return Agent(
        get_triage_model(),
        output_type=ClassificationAgentOutput,
        system_prompt=(
            "You are a triage classifier. Given an error message and context, "
            "return a short classification label (one word or snake_case) and a severity score from 0.0 to 1.0."
        ),
    )
