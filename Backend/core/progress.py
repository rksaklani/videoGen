"""Real-time progress tracking for diffusion generation."""
import threading
from loguru import logger


class ProgressTracker:
    """Thread-safe progress tracker that hooks into the diffusion pipeline."""

    def __init__(self, callback=None):
        self._step = 0
        self._total = 0
        self._phase = "idle"
        self._lock = threading.Lock()
        self._callback = callback

    @property
    def progress(self) -> float:
        with self._lock:
            if self._total == 0:
                return 0.0
            # Map diffusion steps to 0.1-0.9 range (leaving room for pre/post processing)
            step_progress = self._step / self._total
            return 0.1 + step_progress * 0.8

    @property
    def message(self) -> str:
        with self._lock:
            if self._phase == "preprocessing":
                return "Preprocessing inputs..."
            elif self._phase == "encoding":
                return "Encoding reference image..."
            elif self._phase == "diffusion":
                return f"Generating: step {self._step}/{self._total}"
            elif self._phase == "decoding":
                return "Decoding video frames..."
            elif self._phase == "saving":
                return "Saving and encoding video..."
            return "Processing..."

    def set_phase(self, phase: str):
        with self._lock:
            self._phase = phase
        self._notify()

    def update_step(self, step: int, total: int):
        with self._lock:
            self._step = step
            self._total = total
            self._phase = "diffusion"
        self._notify()

    def _notify(self):
        if self._callback:
            try:
                self._callback(self.progress, self.message)
            except Exception:
                pass


def patch_pipeline_progress(pipeline, tracker: ProgressTracker):
    """Monkey-patch the pipeline's progress_bar to report to our tracker."""
    original_progress_bar = pipeline.progress_bar

    class TrackedProgressBar:
        def __init__(self, total=None, **kwargs):
            self.total = total or 0
            self.n = 0
            tracker.update_step(0, self.total)

        def update(self, n=1):
            self.n += n
            tracker.update_step(self.n, self.total)

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    def patched_progress_bar(total=None, **kwargs):
        return TrackedProgressBar(total=total, **kwargs)

    pipeline.progress_bar = patched_progress_bar
    return pipeline
