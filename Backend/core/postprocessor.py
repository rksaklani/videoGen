"""Output postprocessing — video saving, stitching, audio merge, encoding."""
import os
import subprocess
import numpy as np
import imageio
from pathlib import Path
from loguru import logger


def _ffmpeg_bin() -> str:
    return "/usr/bin/ffmpeg" if os.path.exists("/usr/bin/ffmpeg") else "ffmpeg"


def _ffprobe_bin() -> str:
    return "/usr/bin/ffprobe" if os.path.exists("/usr/bin/ffprobe") else "ffprobe"


class Postprocessor:
    """Handles all output postprocessing."""

    def save_video(
        self,
        frames: np.ndarray,
        output_path: str,
        fps: int = 25,
        crf: int = None,
        preset: str = None,
    ) -> str:
        """Save numpy frames as H.264 MP4 (universal compatibility)."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        enc_crf = str(23 if crf is None else crf)
        enc_preset = preset if preset else "fast"

        # Save raw first
        raw_path = output_path + ".raw.mp4"
        imageio.mimsave(raw_path, frames, fps=fps)

        # Re-encode to H.264 for universal playback
        try:
            subprocess.run([
                "ffmpeg", "-i", raw_path,
                "-c:v", "libx264", "-preset", enc_preset, "-crf", enc_crf,
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
                    "-c:v", "libx264", "-preset", enc_preset, "-crf", enc_crf,
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

    @staticmethod
    def _media_duration_seconds(path: str) -> float:
        out = subprocess.run(
            [
                _ffprobe_bin(), "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        return float(out.stdout.strip())

    def _xfade_pair(
        self,
        left: str,
        right: str,
        out_path: str,
        crossfade_sec: float,
        crf: int,
        preset: str,
    ) -> None:
        """Blend two clips with matching video xfade + audio acrossfade."""
        d0 = self._media_duration_seconds(left)
        d1 = self._media_duration_seconds(right)
        t = min(
            crossfade_sec,
            max(d0, 0.1) * 0.45,
            max(d1, 0.1) * 0.45,
        )
        t = max(0.04, t)
        offset = max(0.0, d0 - t)
        enc_crf = str(crf)
        fc = (
            f"[0:v][1:v]xfade=transition=fade:duration={t:.5f}:offset={offset:.5f}[v];"
            f"[0:a][1:a]acrossfade=d={t:.5f}[a]"
        )
        ffmpeg = _ffmpeg_bin()
        subprocess.run(
            [
                ffmpeg, "-i", left, "-i", right,
                "-filter_complex", fc,
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", preset, "-crf", enc_crf,
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                out_path, "-y", "-loglevel", "error",
            ],
            check=True,
            timeout=900,
        )

    def _stitch_concat_copy(self, video_paths: list, output_path: str) -> None:
        """Fast path: concat demuxer with stream copy."""
        ffmpeg = _ffmpeg_bin()
        concat_file = output_path + ".concat.txt"
        with open(concat_file, "w") as f:
            for vp in video_paths:
                f.write(f"file '{os.path.abspath(vp)}'\n")
        try:
            subprocess.run(
                [
                    ffmpeg, "-f", "concat", "-safe", "0",
                    "-i", concat_file, "-c", "copy",
                    "-movflags", "+faststart",
                    output_path, "-y", "-loglevel", "quiet",
                ],
                check=True,
                timeout=300,
            )
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)

    def stitch_videos(
        self,
        video_paths: list,
        output_path: str,
        crossfade_seconds: float = 0.0,
        crf: int = None,
        preset: str = None,
    ) -> str:
        """Stitch multiple clips; optional crossfade between chunks for smoother long-form output."""
        if len(video_paths) == 1:
            os.rename(video_paths[0], output_path)
            return output_path

        enc_crf = 23 if crf is None else int(crf)
        enc_preset = preset if preset else "fast"

        originals = {os.path.abspath(p) for p in video_paths}

        if crossfade_seconds and crossfade_seconds > 0:
            try:
                acc = video_paths[0]
                n = len(video_paths)
                for i in range(1, n):
                    is_last = i == n - 1
                    out = output_path if is_last else output_path + f".xf{i}.mp4"
                    self._xfade_pair(
                        acc, video_paths[i], out,
                        crossfade_seconds, enc_crf, enc_preset,
                    )
                    ap = os.path.abspath(acc)
                    if ap not in originals and os.path.exists(acc):
                        os.remove(acc)
                    acc = out
                logger.info(
                    f"Stitched {len(video_paths)} clips with {crossfade_seconds:.2f}s crossfade: {output_path}"
                )
                return output_path
            except Exception as e:
                logger.warning(f"Crossfade stitch failed ({e}), falling back to concat copy")

        # Fast concat (no crossfade) or fallback
        ffmpeg = _ffmpeg_bin()
        try:
            self._stitch_concat_copy(video_paths, output_path)
            logger.info(f"Stitched {len(video_paths)} clips (concat copy): {output_path}")
        except subprocess.CalledProcessError:
            logger.warning("Concat copy failed, re-encoding concat...")
            inputs = []
            for vp in video_paths:
                inputs.extend(["-i", vp])
            n = len(video_paths)
            filter_v = "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[outv]"
            filter_a = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[outa]"
            subprocess.run(
                [
                    ffmpeg, *inputs,
                    "-filter_complex", f"{filter_v};{filter_a}",
                    "-map", "[outv]", "-map", "[outa]",
                    "-c:v", "libx264", "-preset", enc_preset, "-crf", str(enc_crf),
                    "-c:a", "aac", "-movflags", "+faststart",
                    output_path, "-y", "-loglevel", "quiet",
                ],
                check=True,
                timeout=600,
            )

        # Remove crossfade temps if any
        for i in range(1, len(video_paths)):
            tmp = output_path + f".xf{i}.mp4"
            if os.path.exists(tmp):
                os.remove(tmp)

        return output_path
