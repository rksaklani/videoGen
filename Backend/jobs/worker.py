"""Background worker with job queue, concurrency control, and progress tracking."""
import threading
import traceback
import time
from collections import deque
from loguru import logger
from Backend.api.schemas import JobStatus
from Backend.jobs.queue import JobQueue, Job
from Backend.core.engine import AvatarEngine


class Worker:
    """Processes jobs sequentially (GPU can only handle one at a time)."""

    def __init__(self, engine: AvatarEngine, queue: JobQueue):
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

        try:
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
            logger.info(f"Job {job_id} completed in {elapsed:.0f}s: {result['duration']:.1f}s video")

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = traceback.format_exc()
            logger.error(f"Job {job_id} failed after {elapsed:.0f}s: {error_msg}")
            self.queue.update_job(
                job_id, error=str(e),
                message=f"Failed after {elapsed / 60:.1f} min: {str(e)}")

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def is_busy(self) -> bool:
        return self._processing
