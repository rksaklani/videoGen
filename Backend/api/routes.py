"""API endpoints for avatar generation."""
from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from loguru import logger

from Backend.api.schemas import (
    JobResponse, JobStatusResponse,
    HealthResponse, JobStatus, TTSRequest,
)
from Backend.jobs.queue import JobQueue
from Backend.jobs.worker import Worker, ApiOnlyJobRunner
from Backend.utils.storage import Storage
from Backend.core.engine import AvatarEngine
from Backend.core.tts import TTSEngine, VOICE_PRESETS
from Backend.auth.jwt import get_current_user
from Backend.api.limits import MAX_DURATION_SECONDS, MAX_DURATION_HELP
from Backend.utils.ffmpeg_helpers import convert_audio_to_wav_16k_mono
from Backend.api.deps import require_embedded_inference_ready
from Backend.api.job_helpers import enqueue_video_job

router = APIRouter()

# These get injected by main.py
engine: AvatarEngine = None
queue: JobQueue = None
worker: Worker | ApiOnlyJobRunner = None
storage: Storage = None
tts: TTSEngine = None
_worker_mode = "embedded"


def init_routes(
    _engine: AvatarEngine,
    _queue: JobQueue,
    _worker: Worker | ApiOnlyJobRunner,
    _storage: Storage,
    job_worker_mode: str = "embedded",
):
    global engine, queue, worker, storage, tts, _worker_mode
    engine, queue, worker, storage = _engine, _queue, _worker, _storage
    _worker_mode = job_worker_mode
    tts = TTSEngine(output_dir=str(storage.temp_dir))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API and GPU are ready."""
    status = engine.get_status()
    status["queue_pending"] = worker.pending_count
    status["gpu_busy"] = worker.is_busy
    inf = engine.config.get("inference", {})
    gen_lim = {
        "max_output_duration_seconds": inf.get("max_duration_seconds"),
        "chunk_duration_seconds": inf.get("chunk_duration_seconds"),
        "stitch_crossfade_seconds": inf.get("stitch_crossfade_seconds"),
        "output_follows_audio": True,
        "note": "Generated length matches input audio, capped at max_output_duration_seconds unless max_duration is smaller.",
    }
    return HealthResponse(
        status="ready" if status["loaded"] else "loading",
        engine_loaded=status["loaded"],
        worker_mode=_worker_mode,
        gpu=status,
        generation_limits=gen_lim,
    )


@router.post("/generate", response_model=JobResponse)
async def generate_avatar(
    image: UploadFile = File(..., description="Reference image or video"),
    audio: UploadFile = File(None, description="Audio file (optional if uploading video)"),
    prompt: str = Form(default="", description="Scene description"),
    max_duration: float = Form(
        default=0,
        ge=0,
        le=float(MAX_DURATION_SECONDS),
        description=MAX_DURATION_HELP,
    ),
):
    """
    Generate an avatar video.

    **Duration:** Output length follows your **input audio** (or extracted audio from video),
    up to `max_duration` if set, and never longer than the server cap (see `GET /health` → `generation_limits`).

    Supports:
    - Image + Audio → talking avatar
    - Video only → extracts frame + audio automatically
    - Video + Audio → uses video frame with separate audio
    """
    # Validate image/video
    image_ext = Path(image.filename).suffix.lower()
    valid_image = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".avi", ".mov", ".mkv"}
    if image_ext not in valid_image:
        raise HTTPException(400, f"Invalid format: {image_ext}. Use: {valid_image}")

    # Save image/video
    image_bytes = await image.read()
    image_path = storage.save_upload(image_bytes, image_ext)

    # Handle audio
    audio_path = None
    if audio and audio.filename:
        audio_ext = Path(audio.filename).suffix.lower()
        valid_audio = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
        if audio_ext not in valid_audio:
            raise HTTPException(400, f"Invalid audio format: {audio_ext}. Use: {valid_audio}")

        audio_bytes = await audio.read()
        audio_path = storage.save_upload(audio_bytes, audio_ext)

        # Convert non-WAV to WAV
        if audio_ext != ".wav":
            wav_path = str(audio_path).rsplit(".", 1)[0] + ".wav"
            convert_audio_to_wav_16k_mono(str(audio_path), wav_path)
            audio_path = Path(wav_path)
    elif image_ext not in {".mp4", ".avi", ".mov", ".mkv"}:
        raise HTTPException(400, "Audio file required for image input. Upload a video to auto-extract audio.")

    # Create job
    job = enqueue_video_job(
        queue, storage, worker,
        image_path=str(image_path),
        audio_path=str(audio_path) if audio_path else "",
        prompt=prompt,
        max_duration=max_duration,
        enqueue_reason="multipart_generate",
    )

    mode = "video-to-avatar" if image_ext in {".mp4", ".avi", ".mov", ".mkv"} else "image+audio"
    return JobResponse(
        job_id=job.job_id,
        status=JobStatus.QUEUED,
        message=f"Job queued ({mode}). Estimated: {max_duration * 4:.0f}-{max_duration * 6:.0f} min",
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Check the status of a generation job."""
    job = queue.get_job(job_id)
    if not job:
        logger.bind(job_id=job_id).debug("job status lookup miss")
        raise HTTPException(404, f"Job not found: {job_id}")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        result=job.result,
    )


@router.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download the generated video."""
    job = queue.get_job(job_id)
    if not job:
        logger.bind(job_id=job_id).debug("job download lookup miss")
        raise HTTPException(404, f"Job not found: {job_id}")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(400, f"Job not ready. Status: {job.status}")
    if not job.result or not os.path.exists(job.result.get("output_path", "")):
        raise HTTPException(404, "Output file not found")

    return FileResponse(
        job.result["output_path"],
        media_type="video/mp4",
        filename=f"avatar_{job_id}.mp4",
    )


@router.get("/jobs")
async def list_jobs(limit: int = 20):
    """List recent jobs."""
    jobs = queue.list_jobs(limit)
    return [
        {
            "job_id": j.job_id,
            "status": j.status,
            "progress": j.progress,
            "message": j.message,
            "created_at": j.created_at.isoformat(),
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        }
        for j in jobs
    ]


# ==================== TTS Endpoints ====================

@router.get("/tts/voices")
async def list_tts_voices():
    """List available TTS voice presets."""
    return {
        "presets": {k: v for k, v in VOICE_PRESETS.items()},
        "usage": "Use preset key (e.g. 'en-male') or full voice name (e.g. 'en-US-GuyNeural')",
    }


@router.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    """Convert text to speech audio file."""
    try:
        audio_path = tts.generate(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            pitch=request.pitch,
        )
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename="tts_output.wav",
        )
    except Exception as e:
        raise HTTPException(500, f"TTS generation failed: {str(e)}")


@router.post("/generate-from-text", response_model=JobResponse)
async def generate_avatar_from_text(
    image: UploadFile = File(..., description="Reference image or video"),
    text: str = Form(..., description="Text to speak"),
    voice: str = Form(default="en-male", description="Voice preset"),
    prompt: str = Form(default="", description="Scene description"),
    max_duration: float = Form(
        default=0,
        ge=0,
        le=float(MAX_DURATION_SECONDS),
        description=MAX_DURATION_HELP,
    ),
    rate: str = Form(default="+0%", description="Speech speed"),
):
    """
    Generate avatar video from image + TEXT (not audio).
    Text is converted to speech first, then used to drive the avatar.
    This is the HeyGen-like feature.
    """
    # Validate image
    image_ext = Path(image.filename).suffix.lower()
    valid_image = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".avi", ".mov", ".mkv"}
    if image_ext not in valid_image:
        raise HTTPException(400, f"Invalid image format: {image_ext}")

    # Save image
    image_bytes = await image.read()
    image_path = storage.save_upload(image_bytes, image_ext)

    # Generate speech from text
    try:
        audio_path = tts.generate(text=text, voice=voice, rate=rate)
    except Exception as e:
        raise HTTPException(500, f"TTS failed: {str(e)}")

    job = enqueue_video_job(
        queue, storage, worker,
        image_path=str(image_path),
        audio_path=str(audio_path),
        prompt=prompt,
        max_duration=max_duration,
        enqueue_reason="generate_from_text",
    )

    return JobResponse(
        job_id=job.job_id,
        status=JobStatus.QUEUED,
        message=f"Text converted to speech. Video generation queued (~{max_duration * 6:.0f} min)",
    )


# ==================== Optimization Endpoints ====================

@router.get("/optimization/status", dependencies=[Depends(require_embedded_inference_ready)])
async def optimization_status():
    """Get current speed optimization status."""
    from Backend.core.tensorrt_optimizer import SpeedPipeline
    pipeline = SpeedPipeline(engine)
    return pipeline.get_optimization_status()


@router.get("/optimization/profile", dependencies=[Depends(require_embedded_inference_ready)])
async def optimization_profile():
    """Get performance profile of model components."""
    from Backend.core.tensorrt_optimizer import SpeedPipeline
    pipeline = SpeedPipeline(engine)
    return {"report": pipeline.profile_all()}


@router.post("/optimization/apply", dependencies=[Depends(require_embedded_inference_ready)])
async def apply_optimizations():
    """Apply speed optimizations (TensorRT, torch.compile where safe)."""
    from Backend.core.tensorrt_optimizer import SpeedPipeline
    pipeline = SpeedPipeline(engine)
    try:
        skip_transformer = engine.infer_cfg.get("cpu_offload", True)
        pipeline.optimize_all(skip_transformer=skip_transformer)
        return {"status": "success", "message": "Optimizations applied", "details": pipeline.get_optimization_status()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==================== Voice Clone Endpoints ====================

@router.post("/voice/clone")
async def clone_voice(
    audio: UploadFile = File(..., description="Reference voice audio (10-60 seconds)"),
    user: dict = Depends(get_current_user),
):
    """Upload a voice sample to create a voice clone profile."""
    from Backend.core.voice_clone import VoiceCloner
    from Backend.core.tts import TTSEngine

    audio_ext = Path(audio.filename).suffix.lower()
    if audio_ext not in {".wav", ".mp3", ".flac", ".ogg"}:
        raise HTTPException(400, f"Invalid audio format: {audio_ext}")

    audio_bytes = await audio.read()
    audio_path = storage.save_upload(audio_bytes, audio_ext)

    # Convert to WAV
    wav_path = str(audio_path).rsplit(".", 1)[0] + ".wav"
    convert_audio_to_wav_16k_mono(str(audio_path), wav_path)

    cloner = VoiceCloner(tts_engine=tts)
    profile = cloner.save_voice_profile(user["email"], wav_path)

    return {"message": "Voice profile created", "profile": profile}


@router.post("/voice/speak")
async def speak_with_cloned_voice(
    text: str = Form(..., description="Text to speak"),
    language: str = Form(default="en"),
    user: dict = Depends(get_current_user),
):
    """Generate speech using your cloned voice."""
    from Backend.core.voice_clone import VoiceCloner

    cloner = VoiceCloner(tts_engine=tts)
    try:
        audio_path = cloner.speak_as_user(user["email"], text, language)
        return FileResponse(audio_path, media_type="audio/wav", filename="cloned_speech.wav")
    except FileNotFoundError:
        raise HTTPException(404, "No voice profile found. Upload a voice sample first.")


# ==================== Video Processing Endpoints ====================

@router.post("/video/upscale", dependencies=[Depends(require_embedded_inference_ready)])
async def upscale_video(
    job_id: str = Form(..., description="Job ID of completed video"),
    target_height: int = Form(default=1080, ge=720, le=2160),
):
    """Upscale a generated video to higher resolution."""
    from Backend.core.upscaler import VideoUpscaler

    job = queue.get_job(job_id)
    if not job or not job.result:
        raise HTTPException(404, "Job not found or not completed")

    input_path = job.result.get("output_path")
    if not input_path or not os.path.exists(input_path):
        raise HTTPException(404, "Video file not found")

    output_path = input_path.replace(".mp4", f"_{target_height}p.mp4")
    upscaler = VideoUpscaler()
    result = upscaler.upscale(input_path, output_path, target_height)

    return FileResponse(result, media_type="video/mp4", filename=f"avatar_{job_id}_{target_height}p.mp4")


@router.post("/video/add-overlay", dependencies=[Depends(require_embedded_inference_ready)])
async def add_video_overlay(
    job_id: str = Form(..., description="Job ID of completed video"),
    overlay: UploadFile = File(..., description="Logo/watermark image"),
    position: str = Form(default="bottom-right"),
):
    """Add a logo or watermark to a generated video."""
    from Backend.core.background import BackgroundProcessor

    job = queue.get_job(job_id)
    if not job or not job.result:
        raise HTTPException(404, "Job not found or not completed")

    input_path = job.result.get("output_path")
    if not input_path or not os.path.exists(input_path):
        raise HTTPException(404, "Video file not found")

    overlay_bytes = await overlay.read()
    overlay_path = storage.save_upload(overlay_bytes, Path(overlay.filename).suffix.lower())

    output_path = input_path.replace(".mp4", "_branded.mp4")
    bg = BackgroundProcessor()
    result = bg.add_overlay(input_path, str(overlay_path), output_path, position)

    return FileResponse(result, media_type="video/mp4", filename=f"avatar_{job_id}_branded.mp4")


# ==================== Multi-Character Dialogue ====================

@router.post("/generate-dialogue", response_model=JobResponse, dependencies=[Depends(require_embedded_inference_ready)])
async def generate_dialogue(
    script: str = Form(..., description="Dialogue script (JSON format)"),
    char_a_image: UploadFile = File(..., description="Character A image"),
    char_b_image: UploadFile = File(None, description="Character B image (optional)"),
    layout: str = Form(default="side-by-side", description="Layout: side-by-side or interview"),
):
    """
    Generate a multi-character dialogue video.

    Script format (JSON string):
    {
        "characters": [
            {"name": "Alice", "voice": "en-female"},
            {"name": "Bob", "voice": "en-male"}
        ],
        "lines": [
            {"character": "Alice", "text": "Hello, how are you?"},
            {"character": "Bob", "text": "I'm doing great, thanks!"},
            {"character": "Alice", "text": "That's wonderful to hear."}
        ],
        "scene_prompt": "Two people talking in a modern studio"
    }

    Or simple text format:
    Alice: Hello, how are you?
    Bob: I'm doing great, thanks!
    """
    import json as json_lib
    from Backend.core.dialogue import DialogueParser, DialogueScript, Character

    # Parse script
    try:
        script_data = json_lib.loads(script)
        parsed = DialogueParser.parse_json(script_data)
    except (json_lib.JSONDecodeError, KeyError):
        # Try simple text format
        lines = DialogueParser.parse_text(script)
        char_names = list(dict.fromkeys(l.character for l in lines))
        parsed = DialogueScript(
            characters=[Character(name=n, image_path="", voice="en-male" if i == 0 else "en-female")
                        for i, n in enumerate(char_names)],
            lines=lines,
        )

    if len(parsed.lines) == 0:
        raise HTTPException(400, "No dialogue lines found in script")

    # Save character images
    img_a_bytes = await char_a_image.read()
    img_a_path = storage.save_upload(img_a_bytes, Path(char_a_image.filename).suffix.lower())

    if len(parsed.characters) > 0:
        parsed.characters[0].image_path = str(img_a_path)

    if char_b_image and char_b_image.filename:
        img_b_bytes = await char_b_image.read()
        img_b_path = storage.save_upload(img_b_bytes, Path(char_b_image.filename).suffix.lower())
        if len(parsed.characters) > 1:
            parsed.characters[1].image_path = str(img_b_path)
    elif len(parsed.characters) > 1:
        # Use same image for character B if not provided
        parsed.characters[1].image_path = str(img_a_path)

    # Create job
    job = queue.create_job(
        image_path=str(img_a_path),
        audio_path="",
        prompt=parsed.scene_prompt,
        max_duration=0,
        output_path="",
    )
    job.output_path = str(storage.get_output_path(job.job_id))
    queue.persist_job(job)
    logger.bind(job_id=job.job_id).info("dialogue_enqueue lines={}", len(parsed.lines))

    # Process in background
    import threading
    def run_dialogue():
        from Backend.core.dialogue import MultiCharacterBuilder
        try:
            queue.update_job(job.job_id, status=JobStatus.PROCESSING,
                             progress=0.05, message="Starting dialogue generation...")
            builder = MultiCharacterBuilder(engine)
            result = builder.generate_dialogue_video(
                script=parsed,
                output_path=job.output_path,
                layout=layout,
                on_progress=lambda p, msg: queue.update_job(
                    job.job_id, progress=p, message=msg),
            )
            import time
            queue.update_job(job.job_id, status=JobStatus.COMPLETED,
                             progress=1.0, message="Dialogue video ready!",
                             result=result)
        except Exception as e:
            logger.bind(job_id=job.job_id).exception("dialogue job failed")
            queue.update_job(job.job_id, error=str(e),
                             message=f"Failed: {str(e)}")

    threading.Thread(target=run_dialogue, daemon=True).start()

    char_names = [c.name for c in parsed.characters]
    return JobResponse(
        job_id=job.job_id,
        status=JobStatus.QUEUED,
        message=f"Dialogue queued: {len(parsed.lines)} lines, characters: {', '.join(char_names)}",
    )


@router.post("/generate-dialogue-simple", response_model=JobResponse, dependencies=[Depends(require_embedded_inference_ready)])
async def generate_dialogue_simple(
    char_a_image: UploadFile = File(..., description="Character A image"),
    char_b_image: UploadFile = File(None, description="Character B image"),
    char_a_name: str = Form(default="Person A"),
    char_b_name: str = Form(default="Person B"),
    char_a_voice: str = Form(default="en-male"),
    char_b_voice: str = Form(default="en-female"),
    dialogue_text: str = Form(..., description="Simple dialogue: 'Name: text' per line"),
    scene_prompt: str = Form(default="Two people having a conversation"),
    layout: str = Form(default="side-by-side"),
):
    """
    Simplified dialogue endpoint — just upload images and type dialogue.

    Example dialogue_text:
        Alice: Hey, have you tried the new restaurant?
        Bob: Not yet, is it good?
        Alice: It's amazing, you should definitely go!
    """
    import json as json_lib
    from Backend.core.dialogue import DialogueParser, DialogueScript, Character

    lines = DialogueParser.parse_text(dialogue_text)
    if not lines:
        raise HTTPException(400, "No dialogue lines found")

    # Build script
    characters = [
        Character(name=char_a_name, image_path="", voice=char_a_voice),
        Character(name=char_b_name, image_path="", voice=char_b_voice),
    ]

    # Save images
    img_a_bytes = await char_a_image.read()
    img_a_path = storage.save_upload(img_a_bytes, Path(char_a_image.filename).suffix.lower())
    characters[0].image_path = str(img_a_path)

    if char_b_image and char_b_image.filename:
        img_b_bytes = await char_b_image.read()
        img_b_path = storage.save_upload(img_b_bytes, Path(char_b_image.filename).suffix.lower())
        characters[1].image_path = str(img_b_path)
    else:
        characters[1].image_path = str(img_a_path)

    script = DialogueScript(characters=characters, lines=lines, scene_prompt=scene_prompt)

    # Reuse the main dialogue endpoint logic
    job = queue.create_job(
        image_path=str(img_a_path), audio_path="",
        prompt=scene_prompt, max_duration=0, output_path="",
    )
    job.output_path = str(storage.get_output_path(job.job_id))
    queue.persist_job(job)
    logger.bind(job_id=job.job_id).info("dialogue_simple_enqueue lines={}", len(lines))

    import threading
    def run():
        from Backend.core.dialogue import MultiCharacterBuilder
        try:
            queue.update_job(job.job_id, status=JobStatus.PROCESSING,
                             progress=0.05, message="Starting dialogue...")
            builder = MultiCharacterBuilder(engine)
            result = builder.generate_dialogue_video(
                script=script, output_path=job.output_path, layout=layout,
                on_progress=lambda p, msg: queue.update_job(job.job_id, progress=p, message=msg))
            queue.update_job(job.job_id, status=JobStatus.COMPLETED,
                             progress=1.0, message="Done!", result=result)
        except Exception as e:
            logger.bind(job_id=job.job_id).exception("dialogue_simple job failed")
            queue.update_job(job.job_id, error=str(e), message=f"Failed: {str(e)}")

    threading.Thread(target=run, daemon=True).start()

    return JobResponse(
        job_id=job.job_id, status=JobStatus.QUEUED,
        message=f"Dialogue: {len(lines)} lines, {char_a_name} + {char_b_name}",
    )


# ==================== Video Reference → Avatar ====================

@router.post("/create-avatar-from-video", response_model=JobResponse)
async def create_avatar_from_video(
    video: UploadFile = File(..., description="Reference video of a person talking"),
    text: str = Form(None, description="New text for the avatar to speak (optional)"),
    voice: str = Form(default="", description="Voice preset (auto-detected from video if empty)"),
    prompt: str = Form(default="", description="Scene description"),
    max_duration: float = Form(
        default=0,
        ge=0,
        le=float(MAX_DURATION_SECONDS),
        description=MAX_DURATION_HELP,
    ),
    mode: str = Form(default="reanimate", description="'reanimate' = use video's audio, 'new-script' = use provided text"),
):
    """
    Upload a reference video → system extracts face + audio → generates avatar video.

    Modes:
    - 'reanimate': Re-animates the person using the video's own audio (improves quality)
    - 'new-script': Extracts face from video, generates new speech from provided text

    This is the HeyGen-like flow:
    1. Upload video of yourself talking
    2. System extracts your face as reference
    3. Either re-animate with original audio OR speak new text
    """
    video_ext = Path(video.filename).suffix.lower()
    if video_ext not in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
        raise HTTPException(400, f"Invalid video format: {video_ext}. Use MP4, AVI, MOV, MKV, or WEBM")

    # Save video
    video_bytes = await video.read()
    video_path = storage.save_upload(video_bytes, video_ext)

    if mode == "new-script" and not text:
        raise HTTPException(400, "Text is required when mode is 'new-script'")

    audio_path = None
    if mode == "new-script" and text:
        # Generate new speech from text
        detected_voice = voice if voice else "en-male"
        try:
            audio_path = tts.generate(text=text, voice=detected_voice)
        except Exception as e:
            raise HTTPException(500, f"TTS failed: {str(e)}")

    # Create job — engine.generate handles video input automatically
    job = enqueue_video_job(
        queue, storage, worker,
        image_path=str(video_path),
        audio_path=str(audio_path) if audio_path else "",
        prompt=prompt,
        max_duration=max_duration,
        enqueue_reason="create_avatar_from_video",
    )

    mode_desc = "re-animating with original audio" if mode == "reanimate" else "speaking new text"
    return JobResponse(
        job_id=job.job_id,
        status=JobStatus.QUEUED,
        message=f"Video reference received. {mode_desc.capitalize()}.",
    )


@router.post("/extract-from-video", dependencies=[Depends(require_embedded_inference_ready)])
async def extract_from_video(
    video: UploadFile = File(..., description="Video to extract frame and audio from"),
):
    """
    Extract the best frame and audio from a video.
    Returns paths to the extracted files — useful for preview before generation.
    """
    video_ext = Path(video.filename).suffix.lower()
    if video_ext not in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
        raise HTTPException(400, f"Invalid video format: {video_ext}")

    video_bytes = await video.read()
    video_path = storage.save_upload(video_bytes, video_ext)

    from Backend.core.preprocessor import Preprocessor
    preprocessor = engine.preprocessor

    # Extract frame
    frame_path = preprocessor.extract_frame_from_video(str(video_path))

    # Extract audio
    try:
        audio_path = preprocessor.extract_audio_from_video(str(video_path))
        audio_duration = preprocessor.get_audio_duration(audio_path)
    except Exception:
        audio_path = None
        audio_duration = 0

    return {
        "frame_path": frame_path,
        "audio_path": audio_path,
        "audio_duration": audio_duration,
        "message": "Frame and audio extracted successfully",
    }
