"""Load environment variables before other app imports read ``os.environ``.

Order:
1. Repository root ``.env`` (shared defaults)
2. ``Backend/.env`` (backend overrides — wins on conflicts)
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parent


def load_application_env() -> None:
    """Populate ``os.environ`` from dotenv files (does not override existing real env)."""
    load_dotenv(_REPO_ROOT / ".env", override=False)
    load_dotenv(_BACKEND_DIR / ".env", override=True)
