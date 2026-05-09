"""
Multi-Character Dialogue System.

Parses dialogue scripts, generates audio per character,
mixes audio tracks with timing, and builds multi-character batches.
"""
import os
import re
import json
import uuid
import subprocess
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from loguru import logger


@dataclass
class DialogueLine:
    """A single line of dialogue."""
    character: str          # Character name (e.g. "Alice")
    text: str               # What they say
    start_time: float = 0.0 # When this line starts (seconds)
    end_time: float = 0.0   # When this line ends (seconds)
    audio_path: str = ""    # Generated audio file for this line


@dataclass
class Character:
    """A character in the dialogue."""
    name: str
    image_path: str
    voice: str = "en-male"  # TTS voice preset
    audio_path: str = ""    # Pre-recorded audio (optional)


@dataclass
class DialogueScript:
    """Complete dialogue with characters and lines."""
    characters: List[Character] = field(default_factory=list)
    lines: List[DialogueLine] = field(default_factory=list)
    scene_prompt: str = ""
    total_duration: float = 0.0


class DialogueParser:
    """Parse dialogue scripts in various formats."""

    @staticmethod
    def parse_text(script: str) -> List[DialogueLine]:
        """
        Parse a simple text dialogue format:

        Alice: Hello, how are you?
        Bob: I'm doing great, thanks!
        Alice: That's wonderful to hear.
        """
        lines = []
        for line in script.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r'^([^:]+):\s*(.+)$', line)
            if match:
                character = match.group(1).strip()
                text = match.group(2).strip()
                lines.append(DialogueLine(character=character, text=text))
            else:
                # Continuation of previous line
                if lines:
                    lines[-1].text += " " + line
        logger.info(f"Parsed {len(lines)} dialogue lines")
        return lines

    @staticmethod
    def parse_json(data: dict) -> DialogueScript:
        """
        Parse JSON dialogue format:
        {
            "characters": [
                {"name": "Alice", "image": "alice.png", "voice": "en-female"},
                {"name": "Bob", "image": "bob.png", "voice": "en-male"}
            ],
            "lines": [
                {"character": "Alice", "text": "Hello!"},
                {"character": "Bob", "text": "Hi there!"}
            ],
            "scene_prompt": "Two people talking in a studio"
        }
        """
        script = DialogueScript()
        script.scene_prompt = data.get("scene_prompt", "")

        for c in data.get("characters", []):
            script.characters.append(Character(
                name=c["name"],
                image_path=c.get("image", ""),
                voice=c.get("voice", "en-male"),
            ))

        for l in data.get("lines", []):
            script.lines.append(DialogueLine(
                character=l["character"],
                text=l["text"],
            ))

        return script


class AudioMixer:
    """Generate and mix audio tracks for multi-character dialogue."""

    def __init__(self, tts_engine, temp_dir: str = "Backend/data/temp"):
        self.tts = tts_engine
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_dialogue_audio(self, script: DialogueScript) -> DialogueScript:
        """Generate TTS audio for each line and calculate timing."""
        current_time = 0.0
        pause_between_lines = 0.3  # 300ms pause between speakers

        for i, line in enumerate(script.lines):
            # Find character's voice
            voice = "en-male"
            for char in script.characters:
                if char.name == line.character:
                    voice = char.voice
                    break

            # Generate audio for this line
            audio_path = str(self.temp_dir / f"dialogue_{uuid.uuid4().hex[:8]}.wav")
            self.tts.generate(text=line.text, voice=voice, output_path=audio_path)

            # Get duration of generated audio
            duration = self._get_audio_duration(audio_path)

            line.audio_path = audio_path
            line.start_time = current_time
            line.end_time = current_time + duration
            current_time = line.end_time + pause_between_lines

            logger.info(f"Line {i+1}: [{line.character}] {line.start_time:.1f}s-{line.end_time:.1f}s '{line.text[:30]}...'")

        script.total_duration = current_time
        return script

    def mix_to_single_track(self, script: DialogueScript, output_path: str) -> str:
        """Mix all dialogue lines into a single audio track with proper timing."""
        if not script.lines:
            raise ValueError("No dialogue lines to mix")

        total_samples = int(script.total_duration * 16000) + 16000  # +1s buffer
        mixed = np.zeros(total_samples, dtype=np.float32)

        for line in script.lines:
            if not line.audio_path or not os.path.exists(line.audio_path):
                continue
            import librosa
            audio, sr = librosa.load(line.audio_path, sr=16000)
            start_sample = int(line.start_time * 16000)
            end_sample = min(start_sample + len(audio), total_samples)
            mixed[start_sample:end_sample] += audio[:end_sample - start_sample]

        # Normalize
        max_val = np.max(np.abs(mixed))
        if max_val > 0:
            mixed = mixed / max_val * 0.9

        # Save as WAV
        import soundfile as sf
        sf.write(output_path, mixed, 16000)
        logger.info(f"Mixed audio: {output_path} ({script.total_duration:.1f}s)")
        return output_path

    def create_per_character_tracks(self, script: DialogueScript) -> dict:
        """Create separate audio tracks per character (for face mask targeting)."""
        char_tracks = {}
        total_samples = int(script.total_duration * 16000) + 16000

        for char in script.characters:
            char_tracks[char.name] = np.zeros(total_samples, dtype=np.float32)

        for line in script.lines:
            if not line.audio_path or not os.path.exists(line.audio_path):
                continue
            if line.character not in char_tracks:
                continue
            import librosa
            audio, sr = librosa.load(line.audio_path, sr=16000)
            start_sample = int(line.start_time * 16000)
            end_sample = min(start_sample + len(audio), total_samples)
            char_tracks[line.character][start_sample:end_sample] += audio[:end_sample - start_sample]

        # Save each track
        import soundfile as sf
        result = {}
        for name, track in char_tracks.items():
            path = str(self.temp_dir / f"char_{name}_{uuid.uuid4().hex[:6]}.wav")
            max_val = np.max(np.abs(track))
            if max_val > 0:
                track = track / max_val * 0.9
            sf.write(path, track, 16000)
            result[name] = path

        return result

    def _get_audio_duration(self, audio_path: str) -> float:
        import librosa
        y, sr = librosa.load(audio_path, sr=16000)
        return len(y) / sr


class MultiCharacterBuilder:
    """Build generation inputs for multi-character scenes."""

    def __init__(self, engine):
        self.engine = engine

    def build_composite_image(self, characters: List[Character],
                               layout: str = "side-by-side",
                               canvas_size: tuple = (1024, 512)) -> str:
        """
        Compose multiple character images into a single scene image.

        Layouts:
        - side-by-side: Characters placed left and right
        - interview: One larger (interviewer), one smaller
        """
        from PIL import Image as PILImage

        canvas_w, canvas_h = canvas_size
        canvas = PILImage.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

        n = len(characters)
        if n == 0:
            raise ValueError("No characters provided")

        if layout == "side-by-side":
            slot_w = canvas_w // n
            for i, char in enumerate(characters):
                if not char.image_path or not os.path.exists(char.image_path):
                    continue
                img = PILImage.open(char.image_path).convert("RGB")
                # Resize to fit slot while maintaining aspect ratio
                img_ratio = img.width / img.height
                slot_ratio = slot_w / canvas_h
                if img_ratio > slot_ratio:
                    new_w = slot_w
                    new_h = int(slot_w / img_ratio)
                else:
                    new_h = canvas_h
                    new_w = int(canvas_h * img_ratio)
                img = img.resize((new_w, new_h), PILImage.LANCZOS)
                # Center in slot
                x = i * slot_w + (slot_w - new_w) // 2
                y = (canvas_h - new_h) // 2
                canvas.paste(img, (x, y))

        elif layout == "interview":
            # First character takes 60%, second takes 40%
            if n >= 2:
                for i, (char, ratio) in enumerate(zip(characters[:2], [0.6, 0.4])):
                    if not char.image_path or not os.path.exists(char.image_path):
                        continue
                    img = PILImage.open(char.image_path).convert("RGB")
                    slot_w = int(canvas_w * ratio)
                    img = img.resize((slot_w, canvas_h), PILImage.LANCZOS)
                    x = 0 if i == 0 else int(canvas_w * 0.6)
                    canvas.paste(img, (x, 0))

        # Save composite
        output_path = str(Path(self.engine.config["storage"]["temp_dir"]) / f"composite_{uuid.uuid4().hex[:8]}.png")
        canvas.save(output_path)
        logger.info(f"Composite image: {output_path} ({canvas_w}x{canvas_h}, {n} characters)")
        return output_path

    def generate_dialogue_video(self, script: DialogueScript,
                                 output_path: str,
                                 layout: str = "side-by-side",
                                 on_progress: callable = None) -> dict:
        """
        Generate a multi-character dialogue video.

        Pipeline:
        1. Generate TTS audio for each line
        2. Mix audio tracks
        3. Build composite image
        4. Generate video with mixed audio
        5. Post-process
        """
        from Backend.core.tts import TTSEngine

        def progress(p, msg):
            if on_progress:
                on_progress(p, msg)

        tts = TTSEngine(output_dir=str(Path(self.engine.config["storage"]["temp_dir"])))
        mixer = AudioMixer(tts, temp_dir=self.engine.config["storage"]["temp_dir"])

        # Step 1: Generate audio for each line
        progress(0.05, "Generating speech for each character...")
        script = mixer.generate_dialogue_audio(script)

        # Step 2: Mix into single track
        progress(0.15, "Mixing audio tracks...")
        mixed_audio = str(Path(self.engine.config["storage"]["temp_dir"]) / f"mixed_{uuid.uuid4().hex[:8]}.wav")
        mixer.mix_to_single_track(script, mixed_audio)

        # Step 3: Build composite image
        progress(0.20, "Composing character scene...")
        composite_image = self.build_composite_image(script.characters, layout)

        # Step 4: Generate video
        progress(0.25, f"Generating {script.total_duration:.0f}s video...")
        result = self.engine.generate(
            image_path=composite_image,
            audio_path=mixed_audio,
            prompt=script.scene_prompt or "Two people having a conversation",
            max_duration=script.total_duration,
            output_path=output_path,
            on_progress=lambda p, msg: progress(0.25 + p * 0.7, msg),
        )

        # Cleanup temp files
        for line in script.lines:
            if line.audio_path and os.path.exists(line.audio_path):
                os.remove(line.audio_path)
        if os.path.exists(mixed_audio):
            os.remove(mixed_audio)
        if os.path.exists(composite_image):
            os.remove(composite_image)

        return result
