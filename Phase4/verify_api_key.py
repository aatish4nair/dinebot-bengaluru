#!/usr/bin/env python3
"""
Phase 4 – Verify GROQ_API_KEY is loaded from the project root .env and optionally test the API.

Run from project root:
  python Phase4/verify_api_key.py

Or from Phase4 directory:
  python verify_api_key.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Load project root .env
_root = Path(__file__).resolve().parent
_env = _root.parent / ".env"
if _env.is_file():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
        print(f"[OK] Loaded .env from {_env}")
    except ImportError:
        print("[--] python-dotenv not installed; using existing environment")
else:
    print(f"[--] No .env at {_env}")

key = os.environ.get("GROQ_API_KEY")
if not key:
    print("[FAIL] GROQ_API_KEY is not set. Add it to the project root .env or set the environment variable.")
    sys.exit(1)
print(f"[OK] GROQ_API_KEY is set (length={len(key)}, prefix={key[:10]}...)")

# Optional: one real API call
try:
    sys.path.insert(0, str(_root.parent))
    from Phase4.groq_client import chat_completion
    response = chat_completion(
        [{"role": "user", "content": "Reply with exactly: Phase4 API OK"}],
        max_tokens=15,
    )
    print(f"[OK] Groq API response: {response[:60]}...")
except Exception as e:
    print(f"[WARN] Groq API call failed: {e}")

print("Phase 4 API key verification done.")
