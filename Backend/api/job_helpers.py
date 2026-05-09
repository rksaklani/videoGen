"""Shared helpers for queuing diffusion jobs (observe + Mongo persist consistently)."""
from __future__ import annotations

from loguru import logger

from Backend.jobs.queue import Job, JobQueue
from Backend.jobs.worker import ApiOnlyJobRunner, Worker
from Backend.utils.storage import Storage


def enqueue_video_job(
    queue: JobQueue,
    storage: Storage,
    worker: Worker | ApiOnlyJobRunner,
    *,
    image_path: str,
    audio_path: str,
    prompt: str,
    max_duration: float,
    enqueue_reason: str,
) -> Job:
    """Create job, persist output path + Mongo snapshot, enqueue worker, structured log."""
    job = queue.create_job(
        image_path=image_path,
        audio_path=audio_path or "",
        prompt=prompt or "",
        max_duration=max_duration,
        output_path="",
    )
    job.output_path = str(storage.get_output_path(job.job_id))
    queue.persist_job(job)
    logger.bind(job_id=job.job_id).info("job_enqueue reason={}", enqueue_reason)
    worker.process_job(job)
    return job
