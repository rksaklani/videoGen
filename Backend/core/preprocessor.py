"""Input preprocessing — images, audio, video."""
import os
import math
import subprocess
import numpy as np
import torch
import librosa
from pathlib import Path
from PIL import Image
from einops import rearrange
from loguru import logger
import torchvision.transforms as transforms
from torchvision.transforms import ToPILImage


class Preprocessor:
    """Handles all input preprocessing for the avatar pipeline."""

    def __init__(self, feature_extractor, align_instance):
        self.feature_extractor = feature_extractor
        self.align_instance = align_instance
        self.llava_transform = transforms.Compose([
            transforms.Resize((336, 336), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize(
                (0.48145466, 0.4578275, 0.4082107),
                (0.26862954, 0.26130258, 0.27577711)),
        ])

    def extract_frame_from_video(self, video_path: str, output_path: str = None) -> str:
        """Extract the best frame from a video for use as reference."""
        if output_path is None:
            output_path = video_path.rsplit(".", 1)[0] + "_frame.png"
        try:
            # Extract frame at 1 second (usually past any intro)
            subprocess.run([
                "ffmpeg", "-i", video_path, "-ss", "1",
                "-vframes", "1", "-update", "1", output_path,
                "-y", "-loglevel", "quiet"
            ], check=True, timeout=30)
            logger.info(f"Extracted frame from video: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"Frame extraction at 1s failed, trying 0s: {e}")
            subprocess.run([
                "ffmpeg", "-i", video_path,
                "-vframes", "1", "-update", "1", output_path,
                "-y", "-loglevel", "quiet"
            ], check=True, timeout=30)
            return output_path

    def extract_audio_from_video(self, video_path: str, output_path: str = None) -> str:
        """Extract audio track from a video file."""
        if output_path is None:
            output_path = video_path.rsplit(".", 1)[0] + "_audio.wav"
        try:
            subprocess.run([
                "ffmpeg", "-i", video_path, "-vn",
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                output_path, "-y", "-loglevel", "quiet"
            ], check=True, timeout=60)
            logger.info(f"Extracted audio from video: {output_path}")
            return output_path
        except Exception as e:
            raise ValueError(f"Failed to extract audio from video: {e}")

    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds."""
        audio, sr = librosa.load(audio_path, sr=16000)
        return len(audio) / sr

    def split_audio(self, audio_path: str, chunk_seconds: float, output_dir: str) -> list:
        """Split long audio into chunks. Returns list of chunk paths."""
        os.makedirs(output_dir, exist_ok=True)
        duration = self.get_audio_duration(audio_path)
        chunks = []
        start = 0.0
        idx = 0
        while start < duration:
            chunk_path = os.path.join(output_dir, f"chunk_{idx:03d}.wav")
            subprocess.run([
                "ffmpeg", "-i", audio_path, "-ss", str(start),
                "-t", str(chunk_seconds), "-y", chunk_path,
                "-loglevel", "quiet"
            ], check=True, timeout=30)
            chunks.append(chunk_path)
            start += chunk_seconds
            idx += 1
        logger.info(f"Split audio into {len(chunks)} chunks of {chunk_seconds}s each")
        return chunks

    def prepare_image(self, image_path: str, target_size: int) -> dict:
        """Load and resize image, return tensor + metadata."""
        ref_image = Image.open(image_path).convert("RGB")
        w, h = ref_image.size
        scale = target_size / min(w, h)
        new_w = round(w * scale / 64) * 64
        new_h = round(h * scale / 64) * 64

        max_pixels = target_size * target_size
        if new_w * new_h > max_pixels:
            scale = math.sqrt(max_pixels / w / h)
            new_w = round(w * scale / 64) * 64
            new_h = round(h * scale / 64) * 64

        ref_image = ref_image.resize((new_w, new_h), Image.LANCZOS)
        ref_tensor = torch.from_numpy(np.array(ref_image))

        to_pil = ToPILImage()
        pixel_ref = rearrange(ref_tensor.clone().unsqueeze(0), "b h w c -> b c h w")
        pixel_ref_llava = torch.stack(
            [self.llava_transform(to_pil(img)) for img in pixel_ref], dim=0)

        return {
            "pixel_value_ref": pixel_ref.unsqueeze(0).to(dtype=torch.float16),
            "pixel_value_ref_llava": pixel_ref_llava.unsqueeze(0).to(dtype=torch.float16),
            "width": new_w,
            "height": new_h,
        }

    def prepare_audio(self, audio_path: str) -> dict:
        """Load audio and extract features."""
        audio_input, sr = librosa.load(audio_path, sr=16000)
        if sr != 16000:
            raise ValueError(f"Expected 16kHz audio, got {sr}Hz")

        audio_features = []
        window = 750 * 640
        for i in range(0, len(audio_input), window):
            feat = self.feature_extractor(
                audio_input[i:i + window],
                sampling_rate=sr,
                return_tensors="pt",
            ).input_features
            audio_features.append(feat)

        audio_features = torch.cat(audio_features, dim=-1)
        audio_len = len(audio_input) // 640

        return {
            "audio_prompts": audio_features,
            "audio_len": audio_len,
            "duration_seconds": len(audio_input) / sr,
        }

    def build_batch(self, image_data: dict, audio_data: dict,
                    prompt: str, max_frames: int = 129) -> dict:
        """Build a complete batch for inference."""
        if not prompt or prompt.strip() == "":
            prompt = "Authentic, Realistic, Natural, High-quality, Lens-Fixed."
        else:
            prompt = "Authentic, Realistic, Natural, High-quality, Lens-Fixed, " + prompt

        audio_len = min(audio_data["audio_len"], max_frames)
        fps = torch.tensor([25.0], dtype=torch.float16)
        motion_heads = torch.from_numpy(np.array([25] * 4)).unsqueeze(0)
        motion_exps = torch.from_numpy(np.array([30] * 4)).unsqueeze(0)

        return {
            "text_prompt": [prompt],
            "audio_path": [""],
            "image_path": [""],
            "fps": fps.unsqueeze(0),
            "audio_prompts": audio_data["audio_prompts"][0].unsqueeze(0).to(dtype=torch.float16),
            "audio_len": [audio_len],
            "motion_bucket_id_exps": motion_exps,
            "motion_bucket_id_heads": motion_heads,
            "pixel_value_ref": image_data["pixel_value_ref"],
            "pixel_value_ref_llava": image_data["pixel_value_ref_llava"],
        }
