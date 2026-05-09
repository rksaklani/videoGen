"""Job queue — in-memory, or persisted in MongoDB when a collection is provided."""
from __future__ import annotations

import uuid
import threading
from datetime import datetime
from typing import Any, Callable, Optional

from loguru import logger
from pymongo.collection import Collection
from pymongo import ReturnDocument

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
        self.result: Optional[dict[str, Any]] = None
        self.created_at = datetime.now()
        self.completed_at = None
        self.error = None

    @staticmethod
    def from_doc(doc: dict) -> "Job":
        j = Job(
            job_id=doc["job_id"],
            image_path=doc["image_path"],
            audio_path=doc.get("audio_path") or "",
            prompt=doc.get("prompt") or "",
            max_duration=float(doc.get("max_duration") or 0),
            output_path=doc.get("output_path") or "",
        )
        st = doc.get("status") or JobStatus.QUEUED.value
        try:
            j.status = JobStatus(st)
        except ValueError:
            j.status = JobStatus.QUEUED
        j.progress = float(doc.get("progress") or 0)
        j.message = doc.get("message") or ""
        j.result = doc.get("result")
        j.error = doc.get("error")
        ca = doc.get("created_at")
        if hasattr(ca, "year"):
            j.created_at = ca
        completed = doc.get("completed_at")
        if completed and hasattr(completed, "year"):
            j.completed_at = completed
        return j

    def to_doc(self) -> dict:
        st = self.status.value if isinstance(self.status, JobStatus) else str(self.status)
        return {
            "job_id": self.job_id,
            "image_path": self.image_path,
            "audio_path": self.audio_path,
            "prompt": self.prompt,
            "max_duration": self.max_duration,
            "output_path": self.output_path,
            "status": st,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class JobQueue:
    """Thread-safe queue; optionally backed by MongoDB collection `jobs`."""

    def __init__(self, mongo_coll: Optional[Collection] = None):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._coll: Optional[Collection] = mongo_coll

    def _upsert_job(self, job: Job):
        if not self._coll:
            return
        self._coll.replace_one({"job_id": job.job_id}, job.to_doc(), upsert=True)

    def hydrate(self):
        """Load active jobs after API restart; stale ``processing`` → ``queued``."""
        if not self._coll:
            return
        self._coll.update_many(
            {"status": JobStatus.PROCESSING.value},
            {"$set": {
                "status": JobStatus.QUEUED.value,
                "message": "Requeued after restart",
                "progress": 0.0,
            }},
        )
        with self._lock:
            self._jobs.clear()
        for doc in self._coll.find({"status": JobStatus.QUEUED.value}).sort("created_at", 1):
            job = Job.from_doc(doc)
            with self._lock:
                self._jobs[job.job_id] = job
        with self._lock:
            n = len(self._jobs)
        logger.info(f"Job queue hydrate: {n} active job(s) in memory")

    def claim_next_queued_job(self) -> Optional[Job]:
        """Atomically claim the oldest queued job (standalone GPU worker)."""
        if not self._coll:
            return None
        doc = self._coll.find_one_and_update(
            {"status": JobStatus.QUEUED.value},
            {"$set": {
                "status": JobStatus.PROCESSING.value,
                "message": "Claimed by worker",
                "progress": 0.03,
            }},
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            return None
        job = Job.from_doc(doc)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def create_job(self, image_path: str, audio_path: str,
                   prompt: str, max_duration: float, output_path: str) -> Job:
        job_id = uuid.uuid4().hex[:12]
        job = Job(job_id, image_path, audio_path, prompt, max_duration, output_path)
        with self._lock:
            self._jobs[job_id] = job
        self._upsert_job(job)
        logger.info(f"Created job {job_id}")
        return job

    def persist_job(self, job: Job):
        """Call after mutating a job outside ``update_job`` (e.g. ``output_path``)."""
        with self._lock:
            self._jobs[job.job_id] = job
        self._upsert_job(job)

    def _resolve_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            cached = self._jobs.get(job_id)
        if cached:
            return cached
        if self._coll:
            doc = self._coll.find_one({"job_id": job_id})
            if doc:
                job = Job.from_doc(doc)
                with self._lock:
                    self._jobs[job_id] = job
                return job
        return None

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._resolve_job(job_id)

    def update_job(self, job_id: str, status: JobStatus = None,
                   progress: float = None, message: str = None,
                   result: dict = None, error: str = None,
                   output_path: str = None):
        job = self._resolve_job(job_id)
        if not job:
            logger.warning(f"update_job: unknown job_id {job_id}")
            return
        if status:
            job.status = status
        if progress is not None:
            job.progress = progress
        if message:
            job.message = message
        if result is not None:
            job.result = result
        if error:
            job.error = error
            job.status = JobStatus.FAILED
            if not message:
                job.message = str(error)
        if output_path is not None:
            job.output_path = output_path
        if status == JobStatus.COMPLETED:
            job.completed_at = datetime.now()

        with self._lock:
            self._jobs[job_id] = job
        self._upsert_job(job)

    def list_jobs(self, limit: int = 20) -> list:
        if self._coll:
            docs = self._coll.find().sort("created_at", -1).limit(limit)
            return [Job.from_doc(d) for d in docs]
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def replay_queued_to_worker(self, run: Callable[[Job], None]) -> None:
        """Drain jobs left ``queued`` in memory into an embedded executor (typically ``Worker.process_job``)."""
        with self._lock:
            jobs = [j for j in self._jobs.values() if j.status == JobStatus.QUEUED]
        if not jobs:
            return
        logger.info(f"Replaying {len(jobs)} queued job(s) to embedded worker")
        for job in jobs:
            run(job)
