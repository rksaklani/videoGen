"""Synchronous pymongo handle for JobQueue (Motor is asyncio-only)."""
from __future__ import annotations

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection

_log = logging.getLogger(__name__)


def open_jobs_collection(uri: str, db_name: str, timeout_ms: int = 3000) -> Optional[Collection]:
    """Open `dbname.jobs`; client stays reachable via ``collection.database.client``."""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
        client.admin.command("ping")
        return client[db_name]["jobs"]
    except Exception as e:
        _log.warning("Mongo sync connect failed (%s); job queue in-memory only.", e)
        return None
