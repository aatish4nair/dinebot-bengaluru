"""
Re-export the FastAPI app from its real home so the legacy import path
`Phase5.webapp.server:app` keeps working.

Importing `web.server` runs the real module once; `app` below is the very same
object, not a copy, so routes, templates and startup behaviour are identical to
`uvicorn web.server:app`.
"""
from __future__ import annotations

import sys
from pathlib import Path

# uvicorn is launched from the repo root on Render, but don't rely on that.
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from web.server import app  # noqa: F401  - re-exported for the legacy path

__all__ = ["app"]
