"""
Voice cloning — analyzes reference audio and generates speech in a similar style.

Phase 1 (current): Pitch/speed analysis → matches closest Edge TTS voice
Phase 2 (future): True neural voice cloning with XTTS or OpenVoice

For true cloning, install: pip install TTS
Then set USE_NEURAL_CLONE=True
"""
import os
import asyncio
import numpy as np
import librosa
import subprocess
from pathlib import Path
from loguru import logger
from Backend.core.tts import TTSEngine, VOICE_PRESETS

USE_NEURAL_CLONE = False  # Set True when XTTS is installed


class VoiceCloner:
    """Clone a voice from a reference audio sample."""

    def __init__(self, tts_engine: TTSEngine, clone_dir: str = "Backend/data/voice_clones"):
        self.tts = tts_engine
        self.clone_dir = Path(clone_dir)
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        self._xtts_model = None

    def analyze_voice(self, audio_path: str) -> dict:
        """Analyze voice characteristics from a sample."""
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = pitches[pitches > 0]
            avg_pitch = float(np.median(pitch_values)) if len(pitch_values) > 0 else 150.0

            duration = len(y) / sr
            energy = librosa.feature.rms(y=y)[0]
            peaks = np.sum(np.diff((energy > np.mean(energy)).astype(int)) > 0)
            words_per_min = (peaks / duration) * 60 if duration > 0 else 120

            gender = "male" if avg_pitch < 180 else "female"
            speed = "slow" if words_per_min < 100 else "fast" if words_per_min > 160 else "normal"

            return {
                "avg_pitch": round(avg_pitch, 1),
                "gender": gender,
                "speed": speed,
                "words_per_minute": round(words_per_min, 1),
                "duration_seconds": round(duration, 1),
            }
        except Exception as e:
            logger.warning(f"Voice analysis failed: {e}")
            return {"gender": "male", "speed": "normal", "avg_pitch": 150.0}

    def match_voice(self, analysis: dict, language: str = "en") -> str:
        """Match analyzed voice to closest TTS preset."""
        gender = analysis.get("gender", "male")
        key = f"{language}-{gender}"
        return VOICE_PRESETS.get(key, "en-US-GuyNeural")

    def clone_and_speak(self, reference_audio: str, text: str,
                        language: str = "en", output_path: str = None) -> str:
        """Generate speech that sounds similar to the reference voice."""
        analysis = self.analyze_voice(reference_audio)
        voice = self.match_voice(analysis, language)

        speed = analysis.get("speed", "normal")
        rate = "+0%" if speed == "normal" else "-10%" if speed == "slow" else "+10%"

        # Adjust pitch based on analysis
        pitch_diff = analysis.get("avg_pitch", 150) - 150
        pitch = f"+{int(pitch_diff/5)}Hz" if pitch_diff > 0 else f"{int(pitch_diff/5)}Hz"

        logger.info(f"Voice clone: gender={analysis['gender']}, pitch={analysis['avg_pitch']:.0f}Hz, voice={voice}")
        return self.tts.generate(text=text, voice=voice, output_path=output_path, rate=rate, pitch=pitch)

    def save_voice_profile(self, user_id: str, reference_audio: str) -> dict:
        """Save a voice profile for reuse."""
        analysis = self.analyze_voice(reference_audio)

        # Copy reference audio to clone directory
        profile_dir = self.clone_dir / user_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        ref_path = str(profile_dir / "reference.wav")
        # Convert to WAV 16kHz
        subprocess.run([
            "ffmpeg", "-i", reference_audio, "-ar", "16000", "-ac", "1",
            ref_path, "-y", "-loglevel", "quiet"
        ], check=True, timeout=30)

        profile = {
            "user_id": user_id,
            "reference_audio": ref_path,
            "analysis": analysis,
            "matched_voice": self.match_voice(analysis),
        }

        logger.info(f"Saved voice profile for {user_id}: {analysis}")
        return profile

    def speak_as_user(self, user_id: str, text: str, language: str = "en",
                      output_path: str = None) -> str:
        """Generate speech using a saved voice profile."""
        ref_path = self.clone_dir / user_id / "reference.wav"
        if not ref_path.exists():
            raise FileNotFoundError(f"No voice profile found for user {user_id}")
        return self.clone_and_speak(str(ref_path), text, language, output_path)
