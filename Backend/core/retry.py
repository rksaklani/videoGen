"""Retry logic and error recovery for generation jobs."""
import time
import torch
import functools
from loguru import logger


class RetryConfig:
    def __init__(self, max_retries: int = 2, retry_delay: float = 5.0,
                 reduce_on_oom: bool = True):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.reduce_on_oom = reduce_on_oom


def with_retry(func):
    """Decorator that retries generation on failure.
    On OOM: reduces frames by 25% and retries.
    On other errors: retries with same params after cleanup.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        config = RetryConfig()
        last_error = None

        for attempt in range(config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.warning(f"Retry attempt {attempt}/{config.max_retries}")
                    time.sleep(config.retry_delay)

                return func(self, *args, **kwargs)

            except torch.cuda.OutOfMemoryError as e:
                last_error = e
                logger.error(f"OOM on attempt {attempt + 1}: {e}")

                # Aggressive cleanup
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                import gc
                gc.collect()

                if config.reduce_on_oom and 'max_duration' in kwargs:
                    old_dur = kwargs['max_duration']
                    kwargs['max_duration'] = max(2.0, old_dur * 0.75)
                    logger.info(f"Reducing duration: {old_dur:.1f}s → {kwargs['max_duration']:.1f}s")

            except Exception as e:
                last_error = e
                logger.error(f"Error on attempt {attempt + 1}: {e}")

                torch.cuda.empty_cache()
                import gc
                gc.collect()

        raise RuntimeError(f"Failed after {config.max_retries + 1} attempts: {last_error}")

    return wrapper
