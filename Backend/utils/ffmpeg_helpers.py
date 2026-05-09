"""Safe ffmpeg invocation via subprocess (no shell injection)."""
from pathlib import Path
import subprocess
import os


def _ffmpeg_exe() -> str:
    return "/usr/bin/ffmpeg" if Path("/usr/bin/ffmpeg").exists() else "ffmpeg"


def convert_audio_to_wav_16k_mono(src_path: str, dst_wav_path: str, *, timeout: float = 120) -> None:
    """Convert any supported audio file to mono 16 kHz WAV for the inference pipeline."""
    subprocess.run(
        [
            _ffmpeg_exe(),
            "-i",
            src_path,
            "-ar",
            "16000",
            "-ac",
            "1",
            dst_wav_path,
            "-y",
            "-loglevel",
            "quiet",
        ],
        check=True,
        timeout=timeout,
    )


def mux_video_audio_shortest_then_remove_video(
    temp_video_path: str,
    audio_path: str,
    output_path: str,
    *,
    timeout: float = 300,
) -> None:
    """Merge temp video with audio (-shortest), write output_path, delete temp_video_path."""
    subprocess.run(
        [
            _ffmpeg_exe(),
            "-i",
            temp_video_path,
            "-i",
            audio_path,
            "-shortest",
            output_path,
            "-y",
            "-loglevel",
            "quiet",
        ],
        check=True,
        timeout=timeout,
    )
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)
