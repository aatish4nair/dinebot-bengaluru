"""
Phase 5 – Streamlit UI & Backend Integration.

Provides a UI for preferences and enriched restaurant recommendations with LLM justifications.
"""
from __future__ import annotations

import sys
from pathlib import Path

_phase5_dir = Path(__file__).resolve().parent
_project_root = _phase5_dir.parent
if _project_root.exists() and str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
