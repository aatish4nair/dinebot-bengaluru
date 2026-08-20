"""
Phase 4 – LLM configuration and environment loading.

Loads GROQ_API_KEY from the project root .env and defines LLM settings for Groq chat completions.

Note: Groq has retired the Llama 3.1 model family this pipeline originally targeted
(`llama-3.1-8b-instant` now 404s as `model_not_found`). Defaults to `openai/gpt-oss-20b`,
a currently available fast Groq-hosted model. Check `client.models.list()` if this
also gets retired.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Load .env from the project root so GROQ_API_KEY is available
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.is_file():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        pass  # dotenv optional; rely on environment already set


@dataclass(frozen=True)
class LLMConfig:
    """
    Configuration for Phase 4 LLM orchestration (Groq-hosted chat model).
    """

    # API key: from environment (loaded from the project root .env when possible)
    groq_api_key: str | None = None

    # Model and generation
    model: str = "openai/gpt-oss-20b"
    temperature: float = 0.3
    max_tokens: int = 1024

    # Timeouts and retries
    request_timeout_seconds: float = 60.0
    max_retries: int = 2


def get_llm_config(api_key: str | None = None) -> LLMConfig:
    """Build LLMConfig, using project root .env for GROQ_API_KEY when available."""
    key = api_key or os.environ.get("GROQ_API_KEY")
    return LLMConfig(groq_api_key=key)


LLM_CONFIG = get_llm_config()
