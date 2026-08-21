"""
Tests for ai_explanations Groq client: API key usage and chat completion (mocked).
"""
from unittest.mock import MagicMock, patch

import pytest

from ai_explanations.groq_client import GroqAPIError, chat_completion


def test_groq_client_raises_when_api_key_missing(monkeypatch):
    """GroqAPIError when GROQ_API_KEY is not set."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(GroqAPIError) as exc_info:
        chat_completion(
            [{"role": "user", "content": "Hi"}],
            api_key=None,
        )
    assert "GROQ_API_KEY" in str(exc_info.value)


def test_chat_completion_uses_provided_api_key():
    """chat_completion passes the API key to the Groq client."""
    # Patch at source so the import inside chat_completion gets the mock
    with patch("groq.Groq") as MockGroq:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mocked response"))]
        )
        MockGroq.return_value = mock_instance

        out = chat_completion(
            [{"role": "user", "content": "Hi"}],
            api_key="gsk_test_key_123",
        )
        assert out == "Mocked response"
        MockGroq.assert_called_once_with(api_key="gsk_test_key_123")
