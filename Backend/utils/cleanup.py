"""Automatic file cleanup for uploads, temp files, and old outputs."""
import os
import time
import threading
from pathlib import Path
from loguru import logger


class FileCleanup:
    """Periodically cleans up old files to prevent disk bloat."""

    def __init__(self, dirs: list, max_age_hours: float = 24.0, interval_minutes: float = 30.0):
        self.dirs = [Path(d) for d in dirs]
        self.max_age_seconds = max_age_hours * 3600
        self.interval = interval_minutes * 60
        self._running = False

    def start(self):
        """Start background cleanup thread."""
        self._running = True
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()
        logger.info(f"File cleanup started (max age: {self.max_age_seconds / 3600:.0f}h, interval: {self.interval / 60:.0f}min)")

    def stop(self):
        self._running = False

    def cleanup_now(self) -> dict:
        """Run cleanup immediately. Returns stats."""
        total_removed = 0
        total_bytes = 0
        for d in self.dirs:
            if not d.exists():
                continue
            for f in d.rglob("*"):
                if not f.is_file():
                    continue
                age = time.time() - f.stat().st_mtime
                if age > self.max_age_seconds:
                    size = f.stat().st_size
                    try:
                        f.unlink()
                        total_removed += 1
                        total_bytes += size
                    except Exception as e:
                        logger.warning(f"Failed to delete {f}: {e}")
        if total_removed > 0:
            logger.info(f"Cleaned up {total_removed} files ({total_bytes / 1e6:.1f} MB)")
        return {"files_removed": total_removed, "bytes_freed": total_bytes}

    def _loop(self):
        while self._running:
            try:
                self.cleanup_now()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
            time.sleep(self.interval)
