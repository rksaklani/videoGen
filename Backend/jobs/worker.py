"""Background worker with job queue, concurrency control, and progress tracking."""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import TYPE_CHECKING

from loguru import logger

from Backend.api.schemas import JobStatus
from Backend.jobs.queue import JobQueue, Job

if TYPE_CHECKING:
    from Backend.core.engine import AvatarEngine


class ApiOnlyJobRunner:
    """Enqueue-only mode: persists jobs without running GPU inference (use standalone worker)."""

    def process_job(self, job: Job) -> None:
        pass

    @property
    def pending_count(self) -> int:
        return 0

    @property
    def is_busy(self) -> bool:
        return False


class Worker:
    """Processes jobs sequentially (GPU can only handle one at a time)."""

    def __init__(self, engine: "AvatarEngine", queue: JobQueue):
        self.engine = engine
        self.queue = queue
        self._pending = deque()
        self._processing = False
        self._lock = threading.Lock()

    def process_job(self, job: Job):
        """Add job to pending queue and start processing if idle."""
        with self._lock:
            self._pending.append(job)
            if not self._processing:
                self._processing = True
                thread = threading.Thread(target=self._process_loop, daemon=True)
                thread.start()

    def _process_loop(self):
        """Process jobs one at a time from the queue."""
        while True:
            with self._lock:
                if not self._pending:
                    self._processing = False
                    return
                job = self._pending.popleft()

            self._run_job(job)

    def _run_job(self, job: Job):
        """Execute a single generation job with progress updates."""
        job_id = job.job_id
        start_time = time.time()
        log = logger.bind(job_id=job_id)

        try:
            log.info(
                "job_start max_duration={} image={} audio={}",
                job.max_duration,
                job.image_path,
                job.audio_path or "(none)",
            )
            self.queue.update_job(job_id, status=JobStatus.PROCESSING,
                                  progress=0.05, message="Preprocessing inputs...")

            self.queue.update_job(job_id, progress=0.1,
                                  message="Generating video (this takes a while)...")

            result = self.engine.generate(
                image_path=job.image_path,
                audio_path=job.audio_path,
                prompt=job.prompt,
                max_duration=job.max_duration,
                output_path=job.output_path,
                on_progress=lambda p, msg: self.queue.update_job(
                    job_id, progress=p, message=msg),
            )

            elapsed = time.time() - start_time
            self.queue.update_job(
                job_id, status=JobStatus.COMPLETED,
                progress=1.0,
                message=f"Done! {result['duration']:.1f}s video in {elapsed / 60:.1f} min",
                result=result)
            log.info(
                "job_done elapsed_sec={} video_duration_sec={} output={}",
                f"{elapsed:.0f}",
                f"{result.get('duration', 0):.1f}",
                result.get("output_path", ""),
            )

        except Exception as e:
            elapsed = time.time() - start_time
            log.exception("job_failed elapsed_sec={:.0f}", elapsed)
            self.queue.update_job(
                job_id, error=str(e),
                message=f"Failed after {elapsed / 60:.1f} min: {str(e)}")

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def is_busy(self) -> bool:
        return self._processing
