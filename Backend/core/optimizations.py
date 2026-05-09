"""
Speed, memory, and quality optimizations for the avatar engine.
"""
import os
import gc
import torch
import functools
from loguru import logger


class TextEmbeddingCache:
    """Cache text embeddings to avoid re-encoding the same prompts."""

    def __init__(self, max_size: int = 100):
        self._cache = {}
        self._max_size = max_size

    def get(self, prompt: str):
        return self._cache.get(prompt)

    def put(self, prompt: str, embeddings: dict):
        if len(self._cache) >= self._max_size:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[prompt] = {
            k: v.cpu().clone() if torch.is_tensor(v) else v
            for k, v in embeddings.items()
        }

    def clear(self):
        self._cache.clear()


class MemoryManager:
    """Proactive GPU memory management."""

    @staticmethod
    def cleanup():
        """Aggressive memory cleanup."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    @staticmethod
    def get_free_memory() -> float:
        """Get free GPU memory in GB."""
        if not torch.cuda.is_available():
            return 0.0
        total = torch.cuda.get_device_properties(0).total_memory
        used = torch.cuda.memory_allocated(0)
        return (total - used) / 1e9

    @staticmethod
    def get_used_memory() -> float:
        """Get used GPU memory in GB."""
        if not torch.cuda.is_available():
            return 0.0
        return torch.cuda.memory_allocated(0) / 1e9

    @staticmethod
    def estimate_max_frames(image_size: int, available_gb: float = None) -> int:
        """Estimate max frames that fit in available VRAM."""
        if available_gb is None:
            available_gb = MemoryManager.get_free_memory()

        # Empirical estimates based on RTX 4090 testing
        # Memory per frame scales with resolution^2
        pixels = image_size * image_size
        base_memory_gb = 8.0  # Base model overhead
        per_frame_gb = pixels / (512 * 512) * 0.08  # ~80MB per frame at 512x512

        usable = available_gb - base_memory_gb
        if usable <= 0:
            return 65  # Minimum safe

        max_frames = int(usable / per_frame_gb)
        # Must be 4n+1 for VAE
        max_frames = (max_frames // 4) * 4 + 1
        return max(65, min(max_frames, 513))  # Cap at ~20 seconds


class SpeedOptimizer:
    """Apply speed optimizations to the model pipeline."""

    @staticmethod
    def enable_torch_compile(model, mode="reduce-overhead"):
        """Compile model with torch.compile for 10-30% speedup."""
        try:
            compiled = torch.compile(model, mode=mode)
            logger.info(f"torch.compile enabled (mode={mode})")
            return compiled
        except Exception as e:
            logger.warning(f"torch.compile failed: {e}")
            return model

    @staticmethod
    def enable_channels_last(model):
        """Convert model to channels_last memory format for faster convolutions."""
        try:
            model = model.to(memory_format=torch.channels_last)
            logger.info("Channels-last memory format enabled")
        except Exception:
            pass
        return model

    @staticmethod
    def optimize_attention():
        """Enable optimized attention backends."""
        # Enable flash attention via torch SDPA
        torch.backends.cuda.enable_flash_sdp(True)
        torch.backends.cuda.enable_mem_efficient_sdp(True)
        torch.backends.cuda.enable_math_sdp(False)
        logger.info("Optimized attention backends enabled")

    @staticmethod
    def set_inference_mode():
        """Set global inference optimizations."""
        torch.set_grad_enabled(False)
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        logger.info("Inference mode optimizations set (TF32, cuDNN benchmark)")


class QualityOptimizer:
    """Quality improvement utilities."""

    @staticmethod
    def get_optimal_cfg_schedule(num_steps: int, base_cfg: float = 6.5) -> list:
        """Dynamic CFG schedule — higher at start, lower at end.
        Produces sharper results without artifacts."""
        schedule = []
        for i in range(num_steps):
            progress = i / num_steps
            # Start high, decay to base
            cfg = base_cfg * (1.0 + 0.5 * (1.0 - progress))
            schedule.append(round(cfg, 2))
        return schedule

    @staticmethod
    def get_optimal_steps(duration_seconds: float) -> int:
        """Recommend inference steps based on video duration."""
        if duration_seconds <= 5:
            return 30  # Good quality, reasonable speed
        elif duration_seconds <= 10:
            return 25  # Slightly faster for longer videos
        elif duration_seconds <= 20:
            return 20  # Speed priority for long videos
        else:
            return 15  # Minimum for very long videos
