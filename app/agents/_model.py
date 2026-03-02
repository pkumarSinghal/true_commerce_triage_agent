"""Shared model config for PydanticAI agents (LiteLLM/Ollama)."""

import os

from pydantic_ai_litellm import LiteLLMModel

# Claude (Anthropic): set ANTHROPIC_API_KEY in env to use LITELLM_MODEL=anthropic/claude-3-5-sonnet etc.
# LiteLLM reads ANTHROPIC_API_KEY automatically when the model name is anthropic/...
CLAUDE_API_KEY_ENVAR = "ANTHROPIC_API_KEY"

# Default model; override via LITELLM_MODEL (e.g. ollama/llama3.2, anthropic/claude-3-5-sonnet)
DEFAULT_MODEL_NAME = os.environ.get("LITELLM_MODEL", "ollama/llama3.2")


def get_triage_model() -> LiteLLMModel:
    """Return the LiteLLM model used for triage agents."""
    return LiteLLMModel(model_name=DEFAULT_MODEL_NAME)
