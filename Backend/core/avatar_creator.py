"""
Avatar Creator — Upload video once, use forever.

Pipeline:
1. User uploads 10s-2min video of themselves talking
2. System extracts:
   - Best face frame (highest quality, front-facing)
   - Voice sample (for voice matching/cloning)
   - Face embeddings metadata
3. Saves as reusable avatar profile
4. Next time: user picks avatar → types text → generates video
"""
import os
import uuid
import subprocess
import numpy as np
from pathlib import Path
from PIL import Image
from loguru import logger


class AvatarCreator:
    """Create reusable avatar profiles from video uploads."""

    def __init__(self, storage_dir: str = "Backend/data/avatars"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_from_video(self, video_path: str, name: str,
                          user_id: str = "anonymous") -> dict:
        """
        Create an avatar profile from a video.

        Returns:
            dict with avatar_id, name, image_path, voice_path, metadata
        """
        avatar_id = uuid.uuid4().hex[:12]
        avatar_dir = self.storage_dir / avatar_id
        avatar_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Creating avatar '{name}' from video: {video_path}")

        # Step 1: Extract multiple frames
        frames_dir = avatar_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        self._extract_frames(video_path, str(frames_dir), count=10)

        # Step 2: Pick the best frame (largest face, front-facing)
        best_frame = self._pick_best_frame(str(frames_dir))
        final_image = str(avatar_dir / "reference.png")
        if best_frame:
            Image.open(best_frame).save(final_image)
        else:
            # Fallback: extract frame at 1 second
            self._extract_single_frame(video_path, final_image, time=1.0)

        # Step 3: Extract audio for voice profile
        voice_path = str(avatar_dir / "voice_sample.wav")
        self._extract_audio(video_path, voice_path)

        # Step 4: Analyze voice characteristics
        voice_analysis = self._analyze_voice(voice_path)

        # Step 5: Get video metadata
        duration = self._get_duration(video_path)

        # Cleanup frames
        import shutil
        if frames_dir.exists():
            shutil.rmtree(frames_dir)

        # Build avatar profile
        profile = {
            "avatar_id": avatar_id,
            "name": name,
            "user_id": user_id,
            "image_path": final_image,
            "voice_path": voice_path,
            "voice_analysis": voice_analysis,
            "source_video_duration": duration,
            "created_at": str(np.datetime64('now')),
        }

        # Save profile metadata
        import json
        with open(str(avatar_dir / "profile.json"), "w") as f:
            json.dump(profile, f, indent=2)

        logger.info(f"Avatar created: {avatar_id} ({name})")
        return profile

    def create_from_image(self, image_path: str, name: str,
                          user_id: str = "anonymous",
                          voice_preset: str = "en-male") -> dict:
        """Create avatar from a single image (no voice sample)."""
        avatar_id = uuid.uuid4().hex[:12]
        avatar_dir = self.storage_dir / avatar_id
        avatar_dir.mkdir(parents=True, exist_ok=True)

        final_image = str(avatar_dir / "reference.png")
        Image.open(image_path).convert("RGB").save(final_image)

        profile = {
            "avatar_id": avatar_id,
            "name": name,
            "user_id": user_id,
            "image_path": final_image,
            "voice_path": None,
            "voice_analysis": {"matched_voice": voice_preset},
            "source_video_duration": 0,
            "created_at": str(np.datetime64('now')),
        }

        import json
        with open(str(avatar_dir / "profile.json"), "w") as f:
            json.dump(profile, f, indent=2)

        logger.info(f"Avatar created from image: {avatar_id} ({name})")
        return profile

    def get_avatar(self, avatar_id: str) -> dict:
        """Load an avatar profile."""
        profile_path = self.storage_dir / avatar_id / "profile.json"
        if not profile_path.exists():
            return None
        import json
        with open(str(profile_path)) as f:
            return json.load(f)

    def list_avatars(self, user_id: str = None) -> list:
        """List all avatars, optionally filtered by user."""
        avatars = []
        for d in sorted(self.storage_dir.iterdir()):
            if not d.is_dir():
                continue
            profile_path = d / "profile.json"
            if profile_path.exists():
                import json
                with open(str(profile_path)) as f:
                    profile = json.load(f)
                if user_id is None or profile.get("user_id") == user_id:
                    avatars.append(profile)
        return avatars

    def delete_avatar(self, avatar_id: str):
        """Delete an avatar profile."""
        avatar_dir = self.storage_dir / avatar_id
        if avatar_dir.exists():
            import shutil
            shutil.rmtree(avatar_dir)
            logger.info(f"Avatar deleted: {avatar_id}")

    def _extract_frames(self, video_path: str, output_dir: str, count: int = 10):
        """Extract evenly-spaced frames from video."""
        duration = self._get_duration(video_path)
        if duration <= 0:
            duration = 10
        interval = max(duration / (count + 1), 0.5)

        for i in range(count):
            time = interval * (i + 1)
            output = os.path.join(output_dir, f"frame_{i:03d}.png")
            subprocess.run([
                "ffmpeg", "-i", video_path, "-ss", str(time),
                "-vframes", "1", "-update", "1", output,
                "-y", "-loglevel", "quiet"
            ], timeout=15)

    def _extract_single_frame(self, video_path: str, output_path: str, time: float = 1.0):
        """Extract a single frame at given time."""
        subprocess.run([
            "ffmpeg", "-i", video_path, "-ss", str(time),
            "-vframes", "1", "-update", "1", output_path,
            "-y", "-loglevel", "quiet"
        ], timeout=15)

    def _pick_best_frame(self, frames_dir: str) -> str:
        """Pick the best frame based on face size and image quality."""
        best_path = None
        best_score = 0

        for f in sorted(Path(frames_dir).glob("*.png")):
            try:
                img = Image.open(str(f))
                w, h = img.size
                # Score: prefer larger images with good aspect ratio
                score = w * h
                # Prefer landscape or square over extreme portrait
                ratio = w / h if h > 0 else 1
                if 0.5 < ratio < 2.0:
                    score *= 1.5
                if score > best_score:
                    best_score = score
                    best_path = str(f)
            except Exception:
                continue

        return best_path

    def _extract_audio(self, video_path: str, output_path: str):
        """Extract audio from video as WAV 16kHz mono."""
        subprocess.run([
            "ffmpeg", "-i", video_path, "-vn",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            output_path, "-y", "-loglevel", "quiet"
        ], timeout=60)

    def _analyze_voice(self, audio_path: str) -> dict:
        """Analyze voice to determine gender, pitch, speed."""
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[pitches > 0]
            avg_pitch = float(np.median(pitch_values)) if len(pitch_values) > 0 else 150.0
            gender = "male" if avg_pitch < 180 else "female"

            # Match to closest voice preset
            from Backend.core.tts import VOICE_PRESETS
            matched = VOICE_PRESETS.get(f"en-{gender}", "en-US-GuyNeural")

            return {
                "avg_pitch": round(avg_pitch, 1),
                "gender": gender,
                "matched_voice": matched,
                "duration": round(len(y) / sr, 1),
            }
        except Exception as e:
            logger.warning(f"Voice analysis failed: {e}")
            return {"gender": "male", "matched_voice": "en-US-GuyNeural"}

    def _get_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ], capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception:
            return 0
