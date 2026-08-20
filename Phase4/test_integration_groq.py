"""
Phase 4 integration test: real Groq API call when GROQ_API_KEY is set.

Run from project root: pytest Phase4/test_integration_groq.py -v
Skips if GROQ_API_KEY is not set or Phase 2 gold data is missing.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pytest

from Phase4.config import get_llm_config


def _has_groq_key() -> bool:
    config = get_llm_config()
    return bool(config.groq_api_key and config.groq_api_key.startswith("gsk_"))


def _has_phase2_gold() -> bool:
    gold = _root / "Phase2" / "data" / "gold" / "zomato_gold.parquet"
    return gold.is_file()


@pytest.mark.skipif(not _has_groq_key(), reason="GROQ_API_KEY not set (e.g. in project root .env)")
def test_config_loads_api_key_from_env():
    """Confirm Phase4 config loads GROQ_API_KEY (from .env or environment)."""
    config = get_llm_config()
    assert config.groq_api_key is not None
    assert config.groq_api_key.startswith("gsk_")


@pytest.mark.skipif(not _has_groq_key(), reason="GROQ_API_KEY not set")
def test_groq_chat_completion_real():
    """One real Groq API call to verify key and connectivity."""
    from Phase4.groq_client import chat_completion

    response = chat_completion(
        [{"role": "user", "content": "Reply with exactly: OK"}],
        max_tokens=10,
    )
    assert response
    assert "OK" in response.upper() or len(response) >= 1


@pytest.mark.skipif(not _has_groq_key() or not _has_phase2_gold(), reason="GROQ_API_KEY or Phase 2 gold data missing")
def test_get_enriched_recommendations_end_to_end():
    """Full flow: Phase 3 -> prompt -> Groq -> parsed explanations."""
    from Phase3.schemas import UserPreferences
    from Phase4.llm_recommendation_service import get_enriched_recommendations

    prefs = UserPreferences(
        place="Koramangala",
        min_rating=4.0,
        max_price_for_two=1500,
        cuisines=["North Indian", "Chinese"],
    )
    enriched = get_enriched_recommendations(prefs)
    assert isinstance(enriched, list)
    for item in enriched:
        assert hasattr(item, "restaurant")
        assert hasattr(item, "score")
        assert hasattr(item, "explanation")
        assert len(item.explanation) >= 10
