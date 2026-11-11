"""Minimal .env loading so API keys are picked up without python-dotenv.

The repo ships IIIS_API_KEY in .env, but nothing on the runner path loaded it.
From a clean shell the key resolved to the local-endpoint dummy in
llm/litellm.py and every attack died with a confusing auth error instead of a
missing-key error.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def find_dotenv(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from `start` looking for a .env file."""
    here = (start or Path(__file__).resolve()).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_dotenv(path: Optional[Path] = None) -> None:
    """Load KEY=VALUE pairs into os.environ, never overriding real env vars."""
    path = path or find_dotenv()
    if path is None or not path.is_file():
        return
    try:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:
        # Best-effort: never block startup because of a malformed .env.
        pass
