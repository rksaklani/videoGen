"""
Speed, memory, and quality optimizations for the avatar engine.
"""
import gc
import torch
from loguru import logger


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
        """Free GPU memory in GB (CUDA driver view — better for budgeting than total - allocated)."""
        if not torch.cuda.is_available():
            return 0.0
        free_b, _total_b = torch.cuda.mem_get_info()
        return free_b / 1e9

    @staticmethod
    def get_used_memory() -> float:
        """Get used GPU memory in GB."""
        if not torch.cuda.is_available():
            return 0.0
        return torch.cuda.memory_allocated(0) / 1e9

    @staticmethod
    def estimate_max_frames(
        image_size: int,
        available_gb: float = None,
        hard_cap: int = 513,
    ) -> int:
        """
        Estimate max frames for one diffusion pass (4n+1), capped by hard_cap.

        `available_gb` must be **free** VRAM (models already resident). Older code
        wrongly subtracted a fixed 8GB “base” from free memory and forced a minimum
        of 65 frames — that guaranteed OOM on ~24GB cards at 704px.
        """
        if available_gb is None:
            available_gb = MemoryManager.get_free_memory()

        hard_cap = max(17, int(hard_cap))
        hard_cap = (hard_cap // 4) * 4 + 1

        # Free VRAM already accounts for loaded weights; only reserve a little for spikes / fragmentation.
        reserve_gb = 0.75
        usable = max(0.0, available_gb - reserve_gb)

        pixels = image_size * image_size
        # Conservative GB per frame at this spatial size (diffusion activations + VAE decode).
        per_frame_gb = pixels / (512 * 512) * 0.10

        min_chunk = 17  # 4*4+1; smallest aligned chunk we attempt under pressure

        if usable <= 0:
            return min(min_chunk, hard_cap)

        raw = int(usable / per_frame_gb)
        raw = max(raw, min_chunk)
        max_frames = (raw // 4) * 4 + 1
        return min(max_frames, hard_cap)


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
    def get_optimal_steps(duration_seconds: float, infer_cfg: dict) -> int:
        """Pick diffusion steps using default_steps and optional duration-based ramp-down."""
        base = int(infer_cfg.get("default_steps", 50))
        if not infer_cfg.get("use_dynamic_steps", False):
            return base

        floor = int(infer_cfg.get("dynamic_steps_floor", 28))
        floor = max(12, min(floor, base))

        # Gentler curve than the old defaults — stays nearer to `base` for quality.
        if duration_seconds <= 6:
            steps = base
        elif duration_seconds <= 14:
            steps = max(floor, base - 6)
        elif duration_seconds <= 24:
            steps = max(floor, base - 12)
        else:
            steps = max(floor, base - 18)

        return max(floor, min(steps, base))
