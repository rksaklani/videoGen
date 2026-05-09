"""Output postprocessing — video saving, stitching, audio merge, encoding."""
import os
import subprocess
import numpy as np
import imageio
from pathlib import Path
from loguru import logger


class Postprocessor:
    """Handles all output postprocessing."""

    def save_video(self, frames: np.ndarray, output_path: str, fps: int = 25) -> str:
        """Save numpy frames as H.264 MP4 (universal compatibility)."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save raw first
        raw_path = output_path + ".raw.mp4"
        imageio.mimsave(raw_path, frames, fps=fps)

        # Re-encode to H.264 for universal playback
        try:
            subprocess.run([
                "ffmpeg", "-i", raw_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p",  # Maximum compatibility
                "-movflags", "+faststart",  # Web streaming friendly
                output_path, "-y", "-loglevel", "quiet"
            ], check=True, timeout=120)
            os.remove(raw_path)
            logger.info(f"Saved H.264 video: {output_path} ({len(frames)} frames)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # libx264 not available, try system ffmpeg with default codec
            try:
                subprocess.run([
                    "/usr/bin/ffmpeg", "-i", raw_path,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    output_path, "-y", "-loglevel", "quiet"
                ], check=True, timeout=120)
                os.remove(raw_path)
                logger.info(f"Saved H.264 video (system ffmpeg): {output_path}")
            except Exception:
                # Last resort: use raw imageio output
                if os.path.exists(raw_path):
                    os.rename(raw_path, output_path)
                logger.warning(f"H.264 encoding failed, using raw output: {output_path}")

        return output_path

    def merge_audio(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Merge audio track into video file with proper encoding."""
        try:
            # Use system ffmpeg for H.264 support
            ffmpeg = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"
            subprocess.run([
                ffmpeg, "-i", video_path, "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-shortest", "-movflags", "+faststart",
                output_path, "-y", "-loglevel", "quiet"
            ], check=True, timeout=120)
            logger.info(f"Merged audio: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio merge failed: {e}")
            return video_path

    def stitch_videos(self, video_paths: list, output_path: str) -> str:
        """Stitch multiple clips with crossfade blending at boundaries."""
        if len(video_paths) == 1:
            os.rename(video_paths[0], output_path)
            return output_path

        ffmpeg = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"

        # Try concat demuxer first (fastest, no re-encode)
        concat_file = output_path + ".concat.txt"
        with open(concat_file, "w") as f:
            for vp in video_paths:
                f.write(f"file '{os.path.abspath(vp)}'\n")

        try:
            subprocess.run([
                ffmpeg, "-f", "concat", "-safe", "0",
                "-i", concat_file, "-c", "copy",
                "-movflags", "+faststart",
                output_path, "-y", "-loglevel", "quiet"
            ], check=True, timeout=300)
            logger.info(f"Stitched {len(video_paths)} clips: {output_path}")
        except subprocess.CalledProcessError:
            # Fallback: re-encode with filter_complex
            logger.warning("Concat failed, re-encoding...")
            inputs = []
            for vp in video_paths:
                inputs.extend(["-i", vp])
            n = len(video_paths)
            filter_v = "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[outv]"
            filter_a = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[outa]"
            subprocess.run([
                ffmpeg, *inputs,
                "-filter_complex", f"{filter_v};{filter_a}",
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-movflags", "+faststart",
                output_path, "-y", "-loglevel", "quiet"
            ], check=True, timeout=600)
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)

        return output_path

    def blend_frame_transition(self, frames_a: np.ndarray, frames_b: np.ndarray,
                                overlap: int = 5) -> np.ndarray:
        """Blend the last N frames of clip A with first N frames of clip B."""
        if overlap <= 0 or len(frames_a) < overlap or len(frames_b) < overlap:
            return np.concatenate([frames_a, frames_b], axis=0)

        blended = []
        # Keep all frames before overlap
        blended.extend(frames_a[:-overlap])

        # Blend overlap region
        for i in range(overlap):
            alpha = i / overlap
            frame = ((1 - alpha) * frames_a[-(overlap - i)] + alpha * frames_b[i]).astype(np.uint8)
            blended.append(frame)

        # Keep all frames after overlap
        blended.extend(frames_b[overlap:])

        return np.stack(blended, axis=0)
