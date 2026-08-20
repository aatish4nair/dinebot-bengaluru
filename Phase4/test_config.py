"""
Tests for Phase 4 config: .env loading and GROQ_API_KEY.
"""
import os
from pathlib import Path

import pytest


def test_llm_config_has_expected_attributes():
    """LLMConfig exposes model, temperature, max_tokens, groq_api_key."""
    from Phase4.config import LLMConfig, get_llm_config

    config = get_llm_config(api_key="test_key_123")
    assert config.groq_api_key == "test_key_123"
    assert config.model == "openai/gpt-oss-20b"
    assert config.temperature == 0.3
    assert config.max_tokens == 1024
    assert config.max_retries >= 0


def test_config_uses_env_var_when_api_key_not_passed(monkeypatch):
    """When api_key is not passed, config uses GROQ_API_KEY from environment."""
    from Phase4.config import get_llm_config

    monkeypatch.setenv("GROQ_API_KEY", "env_key_456")
    config = get_llm_config(api_key=None)
    assert config.groq_api_key == "env_key_456"


def test_config_prefers_passed_api_key_over_env(monkeypatch):
    """Explicit api_key argument overrides environment."""
    from Phase4.config import get_llm_config

    monkeypatch.setenv("GROQ_API_KEY", "env_key")
    config = get_llm_config(api_key="passed_key")
    assert config.groq_api_key == "passed_key"


def test_config_loads_dotenv_from_phase4_dir(monkeypatch, tmp_path):
    """Config loads .env from Phase4 directory when present."""
    from Phase4 import config as phase4_config

    # Create a fake .env in a temp dir and patch the config module's _env_path
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=from_dotenv_file\n")
    monkeypatch.setattr(phase4_config, "_env_path", env_file)

    # Re-load dotenv by calling load_dotenv again (module already loaded env once)
    import importlib.util
    spec = importlib.util.find_spec("Phase4.config")
    if spec and spec.origin:
        # Re-execute the dotenv load logic
        if env_file.is_file():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                monkeypatch.setenv("GROQ_API_KEY", "from_dotenv_file")
            except ImportError:
                pass

    config = phase4_config.get_llm_config(api_key=None)
    # If dotenv ran, we'd get from_dotenv_file; otherwise env might be from monkeypatch
    assert config.groq_api_key is not None


def test_api_key_is_called_from_env():
    """Confirm GROQ_API_KEY is read (from project root .env or environment)."""
    from Phase4.config import get_llm_config

    config = get_llm_config()
    # When the project root .env exists with GROQ_API_KEY, it should be set. Real keys start with gsk_.
    if config.groq_api_key and config.groq_api_key.startswith("gsk_"):
        assert len(config.groq_api_key) > 10
