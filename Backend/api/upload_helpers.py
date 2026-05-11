"""Upload size checks shared by API routers."""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from Backend.utils.storage import Storage


def save_upload_limited(
    storage: Storage,
    file_bytes: bytes,
    extension: str,
    *,
    max_bytes: int | None,
) -> Path:
    """Persist upload or raise ``413`` if it exceeds ``max_bytes``."""
    try:
        return storage.save_upload(file_bytes, extension, max_bytes=max_bytes)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
