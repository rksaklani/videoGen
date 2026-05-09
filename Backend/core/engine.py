"""Core avatar generation engine — clean wrapper around VideoGen."""
import os
import gc
import sys
import yaml
import torch
import numpy as np
from pathlib import Path
from loguru import logger
from einops import rearrange

# Add project root to path (parent of Backend)
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from .preprocessor import Preprocessor
from .postprocessor import Postprocessor
from .optimizations import MemoryManager, SpeedOptimizer, QualityOptimizer
from .retry import with_retry
from .progress import ProgressTracker, patch_pipeline_progress


class AvatarEngine:
    """Production wrapper around VideoGen inference."""

    def __init__(self, config_path: str = "Backend/config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.model_cfg = self.config["model"]
        self.infer_cfg = self.config["inference"]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.sampler = None
        self.wav2vec = None
        self.preprocessor = None
        self.postprocessor = Postprocessor()
        self.memory = MemoryManager()
        self._default_infer_steps = int(self.infer_cfg.get("default_steps", 50))
        self._loaded = False

    def load_models(self):
        """Load all models into memory. Call once at startup."""
        if self._loaded:
            logger.info("Models already loaded, skipping")
            return

        logger.info("Loading avatar models...")
        base = self.model_cfg["base_path"]
        # Set MODEL_BASE for the engine's constants.py (expects path without /ckpts)
        os.environ["MODEL_BASE"] = base.replace("/ckpts", "")

        # Set environment for the original codebase
        if self.infer_cfg.get("cpu_offload", True):
            os.environ["CPU_OFFLOAD"] = "1"
        elif "CPU_OFFLOAD" in os.environ:
            del os.environ["CPU_OFFLOAD"]
        os.environ["DISABLE_SP"] = "1"
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

        # Build args for the original codebase
        from Backend.engine.config import parse_args
        ckpt_path = os.path.join(base, self.model_cfg["checkpoint"])
        cli_args = [
            "--ckpt", ckpt_path,
            "--input", "assets/test.csv",
            "--save-path", "./data/outputs",
            "--sample-n-frames", str(self.infer_cfg["max_frames"]),
            "--seed", str(self.infer_cfg["default_seed"]),
            "--image-size", str(self.infer_cfg["default_image_size"]),
            "--cfg-scale", str(self.infer_cfg["default_cfg_scale"]),
            "--infer-steps", str(self.infer_cfg["default_steps"]),
            "--use-deepcache", "1" if self.infer_cfg["use_deepcache"] else "0",
            "--flow-shift-eval-video", "5.0",
        ]
        if self.model_cfg.get("use_fp8", True):
            cli_args.append("--use-fp8")
        if self.infer_cfg.get("cpu_offload", True):
            cli_args.append("--cpu-offload")

        old_argv = sys.argv
        sys.argv = ["engine"] + cli_args
        args = parse_args()
        sys.argv = old_argv

        # Load main sampler
        from Backend.engine.sample_inference_audio import HunyuanVideoSampler
        self.sampler = HunyuanVideoSampler.from_pretrained(
            ckpt_path, args=args, device=self.device)
        self.args = self.sampler.args
        self._default_infer_steps = int(self.infer_cfg["default_steps"])

        # Apply CPU offloading
        if self.infer_cfg.get("cpu_offload", True):
            from diffusers.hooks import apply_group_offloading
            apply_group_offloading(
                self.sampler.pipeline.transformer,
                onload_device=self.device,
                offload_type="block_level",
                num_blocks_per_group=1)

        # Load Whisper
        from transformers import WhisperModel, AutoFeatureExtractor
        whisper_path = os.path.join(base, self.model_cfg["whisper"])
        self.wav2vec = WhisperModel.from_pretrained(whisper_path).to(
            device=self.device, dtype=torch.float32)
        self.wav2vec.requires_grad_(False)
        feature_extractor = AutoFeatureExtractor.from_pretrained(whisper_path)

        # Load face detector
        from Backend.engine.data_kits.face_align import AlignImage
        det_path = os.path.join(base, self.model_cfg["face_detector"])
        align_instance = AlignImage("cuda", det_path=det_path)

        # Create preprocessor
        self.preprocessor = Preprocessor(feature_extractor, align_instance)
        self.feature_extractor = feature_extractor

        # Apply speed optimizations
        SpeedOptimizer.set_inference_mode()
        SpeedOptimizer.optimize_attention()

        # torch.compile for 10-20% speedup (skip if CPU offloading — incompatible)
        if not self.infer_cfg.get("cpu_offload", True):
            try:
                self.sampler.pipeline.transformer = torch.compile(
                    self.sampler.pipeline.transformer, mode="reduce-overhead")
                logger.info("torch.compile applied to transformer (10-20% speedup)")
            except Exception as e:
                logger.warning(f"torch.compile failed (non-critical): {e}")

        self._loaded = True
        logger.info(f"All models loaded! Free VRAM: {self.memory.get_free_memory():.1f}GB")

    @with_retry
    def generate(self, image_path: str, audio_path: str,
                 prompt: str = "", max_duration: float = 5.0,
                 output_path: str = None,
                 on_progress: callable = None) -> dict:
        """
        Generate an avatar video from image/video + audio.

        Supports:
        - Image + Audio → avatar video
        - Video input → auto-extracts best frame (+ audio if no audio provided)
        - Long audio → auto-chunks and stitches

        Args:
            image_path: Path to reference image or video
            audio_path: Path to audio file (WAV/MP3) or None for video input
            prompt: Scene description
            max_duration: Max video duration in seconds
            output_path: Where to save the result
            on_progress: Callback(progress: float, message: str)
        """
        if not self._loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")

        def progress(p, msg):
            if on_progress:
                on_progress(p, msg)

        video_extensions = (".mp4", ".avi", ".mov", ".mkv", ".webm")

        # Handle video input
        if image_path.lower().endswith(video_extensions):
            logger.info(f"Video input detected: {image_path}")
            progress(0.02, "Extracting frame from video...")

            # Extract audio from video if no separate audio provided
            if not audio_path or not os.path.exists(audio_path):
                progress(0.03, "Extracting audio from video...")
                audio_path = self.preprocessor.extract_audio_from_video(image_path)
                logger.info(f"Extracted audio from video: {audio_path}")

            # Extract best frame as reference image
            image_path = self.preprocessor.extract_frame_from_video(image_path)

        if not audio_path or not os.path.exists(audio_path):
            raise ValueError("No audio file provided or extracted")

        # Audio duration = Video duration (no artificial cap)
        audio_duration = self.preprocessor.get_audio_duration(audio_path)
        chunk_sec = self.infer_cfg["chunk_duration_seconds"]
        max_allowed = self.infer_cfg["max_duration_seconds"]

        # max_duration=0 means "match audio length"
        if not max_duration or max_duration <= 0:
            effective_duration = min(audio_duration, max_allowed)
        else:
            effective_duration = min(audio_duration, max_duration, max_allowed)

        logger.info(f"Audio: {audio_duration:.1f}s → Video: {effective_duration:.1f}s")

        if effective_duration > chunk_sec:
            result = self._generate_long(
                image_path, audio_path, prompt,
                effective_duration, output_path, on_progress)
        else:
            progress(0.05, "Starting generation...")
            result = self._generate_single(
                image_path, audio_path, prompt,
                effective_duration, output_path, on_progress)

        # Post-processing: upscale + face enhance
        if result and result.get("output_path") and os.path.exists(result["output_path"]):
            result = self._post_process(result, on_progress)

        return result

    def _post_process(self, result: dict, on_progress: callable = None) -> dict:
        """Apply upscaling and face enhancement to the final video."""
        from .upscaler import VideoUpscaler

        def progress(p, msg):
            if on_progress:
                on_progress(p, msg)

        output_path = result["output_path"]
        upscaler = VideoUpscaler()

        # Upscale to target resolution
        upscale_to = self.infer_cfg.get("upscale_to", 0)
        if upscale_to and upscale_to > 0:
            progress(0.92, f"Upscaling to {upscale_to}p...")
            upscaled_path = output_path.replace(".mp4", f"_{upscale_to}p.mp4")
            upscaler.upscale(output_path, upscaled_path, upscale_to)
            if os.path.exists(upscaled_path) and os.path.getsize(upscaled_path) > 0:
                os.remove(output_path)
                os.rename(upscaled_path, output_path)
                logger.info(f"Upscaled to {upscale_to}p")

        # Face enhancement
        if self.infer_cfg.get("enhance_face", False):
            progress(0.96, "Enhancing facial details...")
            enhanced_path = output_path.replace(".mp4", "_enhanced.mp4")
            upscaler.enhance_face(output_path, enhanced_path)
            if os.path.exists(enhanced_path) and os.path.getsize(enhanced_path) > 0:
                os.remove(output_path)
                os.rename(enhanced_path, output_path)
                logger.info("Face enhancement applied")

        progress(0.98, "Finalizing...")
        return result

    def _generate_single(self, image_path: str, audio_path: str,
                         prompt: str, max_duration: float,
                         output_path: str, on_progress: callable = None) -> dict:
        """Generate a single short clip using the original data pipeline."""
        logger.info(f"Generating single clip: image={image_path}, audio={audio_path}")
        logger.info(f"Free VRAM before generation: {self.memory.get_free_memory():.1f}GB")

        optimal_steps = QualityOptimizer.get_optimal_steps(max_duration, self.infer_cfg)
        if optimal_steps != self.args.infer_steps:
            logger.info(
                f"Inference steps: {self.args.infer_steps} → {optimal_steps} "
                f"(duration {max_duration:.1f}s, dynamic={self.infer_cfg.get('use_dynamic_steps', False)})"
            )
            self.args.infer_steps = optimal_steps

        # Setup progress tracking
        tracker = ProgressTracker(callback=on_progress)
        patch_pipeline_progress(self.sampler.pipeline, tracker)
        tracker.set_phase("preprocessing")

        # Cleanup before starting
        self.memory.cleanup()

        import tempfile
        from torch.utils.data import DataLoader
        from Backend.engine.data_kits.audio_dataset import VideoAudioTextLoaderVal

        # Auto-calculate safe max frames based on available memory
        safe_max = self.memory.estimate_max_frames(
            self.infer_cfg["default_image_size"],
            hard_cap=self.infer_cfg.get("max_vae_frames", 513),
        )
        max_frames = min(int(max_duration * 25), self.infer_cfg["max_frames"], safe_max)
        max_frames = (max_frames // 4) * 4 + 1  # VAE alignment
        logger.info(f"Max frames: {max_frames} (safe limit: {safe_max})")

        # Create a temporary CSV for the original data loader
        tmp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, dir=self.config["storage"]["temp_dir"])
        tmp_csv.write("videoid,image,audio,prompt,fps\n")
        safe_prompt = (prompt or "a person speaking").replace(",", " ")
        tmp_csv.write(f"1,{image_path},{audio_path},{safe_prompt},25\n")
        tmp_csv.close()

        try:
            # Use the original dataset loader (handles text encoding properly)
            dataset = VideoAudioTextLoaderVal(
                image_size=self.infer_cfg["default_image_size"],
                meta_file=tmp_csv.name,
                text_encoder=self.sampler.text_encoder,
                text_encoder_2=self.sampler.text_encoder_2,
                feature_extractor=self.feature_extractor,
            )
            loader = DataLoader(dataset, batch_size=1, shuffle=False)
            batch = next(iter(loader))

            # Cap frames
            batch["audio_len"][0] = min(batch["audio_len"][0], max_frames)

            # Ensure wav2vec is on GPU
            self.wav2vec.to(self.device)

            # Generate
            samples = self.sampler.predict(
                self.args, batch, self.wav2vec,
                self.feature_extractor, self.preprocessor.align_instance)

            if samples is None:
                raise RuntimeError("Generation failed — model returned None")

            # Extract video frames
            sample = samples["samples"][0].unsqueeze(0)
            sample = sample[:, :, :batch["audio_len"][0]]
            video = rearrange(sample[0], "c f h w -> f h w c")
            frames = (video * 255.0).data.cpu().numpy().astype(np.uint8)

            # Get dimensions from batch
            h = batch["pixel_value_ref"].shape[-2]
            w = batch["pixel_value_ref"].shape[-1]

            # Cleanup GPU
            del samples, sample, video
            torch.cuda.empty_cache()
            gc.collect()

            # Save
            temp_video = output_path + ".tmp.mp4" if output_path else "temp_out.mp4"
            self.postprocessor.save_video(
                frames,
                temp_video,
                fps=self.infer_cfg.get("default_fps", 25),
                crf=self.infer_cfg.get("video_encode_crf"),
                preset=self.infer_cfg.get("video_encode_preset"),
            )
            final = self.postprocessor.merge_audio(temp_video, audio_path, output_path)

            if os.path.exists(temp_video):
                os.remove(temp_video)

            return {
                "output_path": final,
                "duration": len(frames) / 25.0,
                "frames": len(frames),
                "width": int(w),
                "height": int(h),
                "status": "success",
            }
        finally:
            os.remove(tmp_csv.name)
            self.args.infer_steps = self._default_infer_steps

    def _generate_long(self, image_path: str, audio_path: str,
                       prompt: str, max_duration: float,
                       output_path: str, on_progress: callable = None) -> dict:
        """Generate a long video by chunking audio and stitching clips."""
        chunk_sec = self.infer_cfg["chunk_duration_seconds"]
        temp_dir = self.config["storage"]["temp_dir"]
        os.makedirs(temp_dir, exist_ok=True)

        def progress(p, msg):
            if on_progress:
                on_progress(p, msg)

        progress(0.05, "Splitting audio into chunks...")

        # Split audio
        chunks = self.preprocessor.split_audio(
            audio_path, chunk_sec, os.path.join(temp_dir, "chunks"))

        # Cap chunks based on max_duration
        max_chunks = int(max_duration / chunk_sec) + 1
        chunks = chunks[:max_chunks]
        total_chunks = len(chunks)

        logger.info(f"Generating {total_chunks} chunks for {max_duration:.1f}s video")

        # Generate each chunk
        clip_paths = []
        total_frames = 0
        for i, chunk_path in enumerate(chunks):
            chunk_progress = 0.1 + (0.85 * i / total_chunks)
            progress(chunk_progress, f"Generating chunk {i + 1}/{total_chunks}...")
            logger.info(f"Generating chunk {i + 1}/{total_chunks}")

            chunk_output = os.path.join(temp_dir, f"clip_{i:03d}.mp4")
            result = self._generate_single(
                image_path, chunk_path, prompt, chunk_sec, chunk_output)
            clip_paths.append(result["output_path"])
            total_frames += result["frames"]

        # Stitch all clips with crossfade blending
        progress(0.95, "Stitching clips with smooth transitions...")
        xf = float(self.infer_cfg.get("stitch_crossfade_seconds", 0.0) or 0.0)
        final = self.postprocessor.stitch_videos(
            clip_paths,
            output_path,
            crossfade_seconds=xf,
            crf=self.infer_cfg.get("video_encode_crf"),
            preset=self.infer_cfg.get("video_encode_preset"),
        )

        # Cleanup chunks
        for cp in chunks + clip_paths:
            if os.path.exists(cp):
                os.remove(cp)

        return {
            "output_path": final,
            "duration": total_frames / 25.0,
            "frames": total_frames,
            "width": 0,
            "height": 0,
            "status": "success",
        }

    def get_status(self) -> dict:
        """Get engine status for health checks."""
        return {
            "loaded": self._loaded,
            "device": str(self.device),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
            "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB" if torch.cuda.is_available() else "N/A",
            "gpu_memory_used": f"{torch.cuda.memory_allocated(0) / 1e9:.1f}GB" if torch.cuda.is_available() else "N/A",
        }
