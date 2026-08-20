"""
Phase 4 – LLM orchestration with Llama 3.1 via Groq.

Enriches Phase 3 recommendations with 2-line natural-language justifications.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path so "from Phase3 ..." works when running from Phase4
_phase4_dir = Path(__file__).resolve().parent
_project_root = _phase4_dir.parent
if _project_root.exists() and str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
