"""File storage management — local now, S3-ready later."""
import os
import uuid
import shutil
from pathlib import Path
from loguru import logger


class Storage:
    def __init__(self, upload_dir: str, output_dir: str, temp_dir: str):
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)

        for d in [self.upload_dir, self.output_dir, self.temp_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_upload(
        self,
        file_bytes: bytes,
        extension: str,
        *,
        max_bytes: int | None = None,
    ) -> Path:
        """Save an uploaded file and return its path."""
        if max_bytes is not None and len(file_bytes) > max_bytes:
            mb = max_bytes / (1024 * 1024)
            raise ValueError(f"File exceeds maximum upload size ({mb:g} MB)")
        filename = f"{uuid.uuid4().hex}{extension}"
        path = self.upload_dir / filename
        path.write_bytes(file_bytes)
        logger.info(f"Saved upload: {path} ({len(file_bytes)} bytes)")
        return path

    def get_output_path(self, job_id: str, extension: str = ".mp4") -> Path:
        """Get the output path for a job."""
        return self.output_dir / f"{job_id}{extension}"

    def get_temp_path(self, prefix: str = "tmp", extension: str = ".mp4") -> Path:
        """Get a temporary file path."""
        return self.temp_dir / f"{prefix}_{uuid.uuid4().hex}{extension}"

    def cleanup_temp(self):
        """Remove all temp files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cleaned up temp directory")

    def file_exists(self, path: Path) -> bool:
        return path.exists() and path.stat().st_size > 0
