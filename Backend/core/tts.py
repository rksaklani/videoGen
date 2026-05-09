"""Text-to-Speech engine using Microsoft Edge TTS (free, high quality, 300+ voices)."""
import os
import uuid
import subprocess
from pathlib import Path
from loguru import logger

VOICE_PRESETS = {
    "en-male": "en-US-GuyNeural",
    "en-female": "en-US-JennyNeural",
    "en-male-uk": "en-GB-RyanNeural",
    "en-female-uk": "en-GB-SoniaNeural",
    "hi-male": "hi-IN-MadhurNeural",
    "hi-female": "hi-IN-SwaraNeural",
    "zh-male": "zh-CN-YunxiNeural",
    "zh-female": "zh-CN-XiaoxiaoNeural",
    "es-male": "es-ES-AlvaroNeural",
    "es-female": "es-ES-ElviraNeural",
    "fr-male": "fr-FR-HenriNeural",
    "fr-female": "fr-FR-DeniseNeural",
    "de-male": "de-DE-ConradNeural",
    "de-female": "de-DE-KatjaNeural",
    "ja-male": "ja-JP-KeitaNeural",
    "ja-female": "ja-JP-NanamiNeural",
    "ko-male": "ko-KR-InJoonNeural",
    "ko-female": "ko-KR-SunHiNeural",
    "ar-male": "ar-SA-HamedNeural",
    "ar-female": "ar-SA-ZariyahNeural",
    "pt-male": "pt-BR-AntonioNeural",
    "pt-female": "pt-BR-FranciscaNeural",
}


class TTSEngine:
    """Convert text to speech using Edge TTS CLI."""

    def __init__(self, output_dir: str = "./Backend/data/temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, text: str, voice: str = "en-US-GuyNeural",
                 output_path: str = None, rate: str = "+0%",
                 pitch: str = "+0Hz") -> str:
        """Convert text to speech and save as WAV."""
        if voice in VOICE_PRESETS:
            voice = VOICE_PRESETS[voice]

        if output_path is None:
            output_path = str(self.output_dir / f"tts_{uuid.uuid4().hex[:8]}.mp3")

        logger.info(f"TTS: '{text[:50]}...' voice={voice}")

        # Run edge-tts CLI (avoids async event loop conflicts with FastAPI)
        cmd = ["edge-tts", "--voice", voice, "--rate", rate, "--pitch", pitch,
               "--text", text, "--write-media", output_path]
        try:
            subprocess.run(cmd, check=True, timeout=60, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"edge-tts failed: {e.stderr.decode()[:200]}")
        except FileNotFoundError:
            raise RuntimeError("edge-tts CLI not found. Install with: pip install edge-tts")

        # Convert MP3 to WAV 16kHz mono
        wav_path = output_path.replace(".mp3", ".wav")
        subprocess.run(
            ["ffmpeg", "-i", output_path, "-ar", "16000", "-ac", "1", wav_path, "-y", "-loglevel", "quiet"],
            timeout=30)

        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
            os.remove(output_path)
            logger.info(f"TTS saved: {wav_path}")
            return wav_path

        return output_path

    def get_presets(self) -> dict:
        return VOICE_PRESETS
