"""
Phase 4 – Map Phase 3 recommendations + preferences to LLM prompt and parse response.

Builds the messages list for Groq and parses the model output into
per-restaurant explanations (2 lines each).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List

_root = Path(__file__).resolve().parent.parent
if _root.exists() and str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from Phase3.schemas import Recommendation, UserPreferences

from .prompt_templates import SYSTEM_INSTRUCTION, build_justification_prompt


def build_messages(preferences: UserPreferences, recommendations: List[Recommendation]) -> List[dict]:
    """
    Build the messages list for Groq chat completions.

    Returns a list of dicts with "role" and "content" for system and user.
    """
    user_content = build_justification_prompt(preferences, recommendations)
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_content},
    ]


def parse_justifications(raw_response: str, recommendations: List[Recommendation]) -> List[str]:
    """
    Parse the LLM response into one explanation string per restaurant, in order.

    Expects lines like "Restaurant 1: ..." or "1. ...". Assigns explanations
    by order: first matching line -> first recommendation, etc.
    Falls back to splitting by double newlines or numbering if needed.
    """
    if not recommendations:
        return []

    lines = raw_response.strip().split("\n")
    # Match "Restaurant 1: ..." or "1. ..." or "1: ..."
    pattern = re.compile(r"^(?:Restaurant\s+)?(\d+)[.:]\s*(.+)$", re.IGNORECASE)
    numbered = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            num = int(m.group(1))
            text = m.group(2).strip()
            numbered.append((num, text))

    # Sort by number and assign by index (1-based number -> 0-based index)
    numbered.sort(key=lambda x: x[0])
    result: List[str] = [""] * len(recommendations)
    for num, text in numbered:
        idx = num - 1
        if 0 <= idx < len(recommendations):
            result[idx] = text

    # Fallback for any missing explanation
    for i in range(len(result)):
        if not result[i].strip():
            result[i] = "Good match for your preferences. Recommended based on rating and cuisine."

    return result
