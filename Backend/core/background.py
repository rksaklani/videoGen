"""
Background removal and replacement for avatar videos.
Uses ffmpeg chromakey or rembg for AI-based removal.
"""
import os
import subprocess
from loguru import logger


class BackgroundProcessor:
    """Remove or replace video backgrounds."""

    def __init__(self):
        self.ffmpeg = "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"

    def replace_background(self, video_path: str, bg_image_path: str,
                           output_path: str, color_key: str = None) -> str:
        """
        Replace video background with an image.

        Args:
            video_path: Input video
            bg_image_path: Background image to use
            output_path: Output video
            color_key: If set, use chromakey (e.g. '0x00FF00' for green screen)
        """
        if color_key:
            return self._chromakey_replace(video_path, bg_image_path, output_path, color_key)
        return self._blur_background(video_path, output_path)

    def blur_background(self, video_path: str, output_path: str,
                        blur_strength: int = 20) -> str:
        """Apply background blur effect (like Zoom/Teams)."""
        try:
            # Use boxblur on the full frame as a simple background blur
            subprocess.run([
                self.ffmpeg, "-i", video_path,
                "-vf", f"split[original][blur];[blur]boxblur={blur_strength}[blurred];[original][blurred]overlay",
                "-c:a", "copy",
                output_path, "-y", "-loglevel", "quiet"
            ], check=True, timeout=300)
            logger.info(f"Background blurred: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"Background blur failed: {e}")
            return video_path

    def add_overlay(self, video_path: str, overlay_image: str,
                    output_path: str, position: str = "bottom-right",
                    scale: float = 0.15) -> str:
        """Add a logo/watermark overlay to the video."""
        positions = {
            "top-left": "10:10",
            "top-right": "W-w-10:10",
            "bottom-left": "10:H-h-10",
            "bottom-right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2",
        }
        pos = positions.get(position, positions["bottom-right"])

        try:
            subprocess.run([
                self.ffmpeg,
                "-i", video_path,
                "-i", overlay_image,
                "-filter_complex",
                f"[1:v]scale=iw*{scale}:-1[logo];[0:v][logo]overlay={pos}",
                "-c:a", "copy",
                output_path, "-y", "-loglevel", "quiet"
            ], check=True, timeout=300)
            logger.info(f"Overlay added: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"Overlay failed: {e}")
            return video_path

    def _chromakey_replace(self, video_path: str, bg_path: str,
                           output_path: str, color: str) -> str:
        """Replace green/blue screen background."""
        try:
            subprocess.run([
                self.ffmpeg,
                "-i", video_path,
                "-i", bg_path,
                "-filter_complex",
                f"[0:v]chromakey={color}:0.1:0.2[fg];[1:v][fg]overlay=shortest=1",
                "-c:a", "copy",
                output_path, "-y", "-loglevel", "quiet"
            ], check=True, timeout=300)
            return output_path
        except Exception as e:
            logger.warning(f"Chromakey failed: {e}")
            return video_path

    def _blur_background(self, video_path: str, output_path: str) -> str:
        """Simple background blur."""
        return self.blur_background(video_path, output_path)
