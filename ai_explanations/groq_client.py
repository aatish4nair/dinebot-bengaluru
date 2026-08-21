"""
ai_explanations – Groq API client for Llama 3.1.

Encapsulates HTTP/chat completion calls to Groq with authentication,
retries, and error handling.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .config import LLMConfig, get_llm_config


class GroqAPIError(Exception):
    """Raised when a Groq API call fails after retries."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


def create_groq_client(api_key: str | None = None):
    """Create a Groq client instance. Uses GROQ_API_KEY from config if api_key not provided."""
    try:
        from groq import Groq
    except ImportError as e:
        raise GroqAPIError(
            "Groq SDK not installed. Install with: pip install groq",
            cause=e,
        ) from e

    config = get_llm_config(api_key=api_key)
    if not config.groq_api_key:
        raise GroqAPIError(
            "GROQ_API_KEY is not set. Add it to the project root .env or set the environment variable."
        )
    return Groq(api_key=config.groq_api_key)


def chat_completion(
    messages: List[Dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    config: LLMConfig | None = None,
    api_key: str | None = None,
) -> str:
    """
    Call Groq chat completions API with retries and timeout.

    Args:
        messages: List of dicts with "role" and "content" (e.g. [{"role": "user", "content": "..."}]).
        model: Override model name.
        temperature: Override temperature.
        max_tokens: Override max tokens.
        config: Use this config; if None, uses get_llm_config(api_key).
        api_key: Optional API key override.

    Returns:
        The assistant message content (single string).

    Raises:
        GroqAPIError: If the API key is missing or the request fails after retries.
    """
    cfg = config or get_llm_config(api_key=api_key)
    if not cfg.groq_api_key:
        raise GroqAPIError(
            "GROQ_API_KEY is not set. Add it to the project root .env or set the environment variable."
        )

    try:
        from groq import Groq
    except ImportError as e:
        raise GroqAPIError(
            "Groq SDK not installed. Install with: pip install groq",
            cause=e,
        ) from e

    client = Groq(api_key=cfg.groq_api_key)
    model_name = model or cfg.model
    temp = temperature if temperature is not None else cfg.temperature
    max_tok = max_tokens if max_tokens is not None else cfg.max_tokens

    extra_kwargs: Dict[str, Any] = {}
    if cfg.reasoning_effort is not None:
        # Reasoning models (e.g. openai/gpt-oss-20b) otherwise spend an
        # unbounded share of max_tokens on hidden chain-of-thought, which can
        # leave zero tokens for the visible answer.
        extra_kwargs["reasoning_effort"] = cfg.reasoning_effort

    last_error: Exception | None = None
    for attempt in range(cfg.max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                timeout=cfg.request_timeout_seconds,
                **extra_kwargs,
            )
            choice = response.choices[0] if response.choices else None
            if not choice or not choice.message:
                raise GroqAPIError("Empty response from Groq API")
            content = (choice.message.content or "").strip()
            if not content and choice.finish_reason == "length":
                # The model exhausted max_tokens (likely on hidden reasoning)
                # before producing any visible text. Treat as a failure so it
                # retries rather than silently returning blank explanations.
                raise GroqAPIError(
                    "Groq response truncated before any content was generated "
                    "(finish_reason=length, empty content) - max_tokens is too low "
                    "for this model's reasoning overhead"
                )
            return content
        except Exception as e:
            last_error = e
            if attempt < cfg.max_retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise GroqAPIError(
                f"Groq API request failed after {cfg.max_retries + 1} attempts: {e}",
                cause=e,
            ) from e

    raise GroqAPIError("Unreachable", cause=last_error)
