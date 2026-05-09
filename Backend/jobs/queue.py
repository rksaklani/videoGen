"""Simple in-memory job queue. Replace with Redis/Celery for production."""
import uuid
import threading
from datetime import datetime
from typing import Optional
from loguru import logger
from Backend.api.schemas import JobStatus


class Job:
    def __init__(self, job_id: str, image_path: str, audio_path: str,
                 prompt: str, max_duration: float, output_path: str):
        self.job_id = job_id
        self.image_path = image_path
        self.audio_path = audio_path
        self.prompt = prompt
        self.max_duration = max_duration
        self.output_path = output_path
        self.status = JobStatus.QUEUED
        self.progress = 0.0
        self.message = "Queued"
        self.result = None
        self.created_at = datetime.now()
        self.completed_at = None
        self.error = None


class JobQueue:
    """Thread-safe in-memory job queue."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, image_path: str, audio_path: str,
                   prompt: str, max_duration: float, output_path: str) -> Job:
        job_id = uuid.uuid4().hex[:12]
        job = Job(job_id, image_path, audio_path, prompt, max_duration, output_path)
        with self._lock:
            self._jobs[job_id] = job
        logger.info(f"Created job {job_id}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def update_job(self, job_id: str, status: JobStatus = None,
                   progress: float = None, message: str = None,
                   result: dict = None, error: str = None):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            if status:
                job.status = status
            if progress is not None:
                job.progress = progress
            if message:
                job.message = message
            if result:
                job.result = result
            if error:
                job.error = error
                job.status = JobStatus.FAILED
            if status == JobStatus.COMPLETED:
                job.completed_at = datetime.now()

    def list_jobs(self, limit: int = 20) -> list:
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]
