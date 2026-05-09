"""
Avatar profile endpoints — Create once, use forever.

Flow:
1. POST /avatars/create-from-video → Upload video → creates avatar
2. POST /avatars/create-from-image → Upload image → creates avatar
3. GET  /avatars/list → See all your avatars
4. POST /avatars/{id}/generate → Pick avatar + type text → get video
"""
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from loguru import logger

from Backend.auth.jwt import get_current_user
from Backend.api.limits import MAX_DURATION_SECONDS, MAX_DURATION_HELP
from Backend.core.avatar_creator import AvatarCreator
from Backend.core.tts import TTSEngine, VOICE_PRESETS
from Backend.api.schemas import JobResponse, JobStatus

router = APIRouter(prefix="/avatars", tags=["Avatars"])

# Injected by main.py
_engine = None
_queue = None
_worker = None
_storage = None
_creator = AvatarCreator()


def init_avatar_routes(engine, queue, worker, storage):
    global _engine, _queue, _worker, _storage
    _engine, _queue, _worker, _storage = engine, queue, worker, storage


@router.post("/create-from-video")
async def create_avatar_from_video(
    video: UploadFile = File(..., description="Video of yourself talking (10s-2min)"),
    name: str = Form(..., description="Avatar name (e.g. 'My Avatar')"),
    user: dict = Depends(get_current_user),
):
    """
    Create a reusable avatar from a video.
    System extracts the best face frame + voice sample.
    """
    ext = Path(video.filename).suffix.lower()
    if ext not in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        raise HTTPException(400, f"Invalid video format: {ext}")

    video_bytes = await video.read()
    video_path = _storage.save_upload(video_bytes, ext)

    try:
        profile = _creator.create_from_video(
            video_path=str(video_path),
            name=name,
            user_id=user["email"],
        )
        return {
            "message": "Avatar created successfully!",
            "avatar": profile,
        }
    except Exception as e:
        raise HTTPException(500, f"Avatar creation failed: {str(e)}")


@router.post("/create-from-image")
async def create_avatar_from_image(
    image: UploadFile = File(..., description="Reference face image"),
    name: str = Form(..., description="Avatar name"),
    voice: str = Form(default="en-male", description="Voice preset"),
    user: dict = Depends(get_current_user),
):
    """Create a reusable avatar from a single image."""
    ext = Path(image.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, f"Invalid image format: {ext}")

    image_bytes = await image.read()
    image_path = _storage.save_upload(image_bytes, ext)

    profile = _creator.create_from_image(
        image_path=str(image_path),
        name=name,
        user_id=user["email"],
        voice_preset=voice,
    )
    return {"message": "Avatar created!", "avatar": profile}


@router.get("/list")
async def list_avatars(user: dict = Depends(get_current_user)):
    """List all your saved avatars."""
    avatars = _creator.list_avatars(user_id=user["email"])
    return {"avatars": avatars, "count": len(avatars)}


@router.get("/{avatar_id}")
async def get_avatar(avatar_id: str):
    """Get avatar details."""
    avatar = _creator.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(404, "Avatar not found")
    return avatar


@router.get("/{avatar_id}/image")
async def get_avatar_image(avatar_id: str):
    """Get avatar's reference image."""
    avatar = _creator.get_avatar(avatar_id)
    if not avatar or not avatar.get("image_path"):
        raise HTTPException(404, "Avatar image not found")
    if not os.path.exists(avatar["image_path"]):
        raise HTTPException(404, "Image file missing")
    return FileResponse(avatar["image_path"], media_type="image/png")


@router.delete("/{avatar_id}")
async def delete_avatar(avatar_id: str, user: dict = Depends(get_current_user)):
    """Delete an avatar."""
    avatar = _creator.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(404, "Avatar not found")
    if avatar.get("user_id") != user["email"] and user["email"] != "anonymous":
        raise HTTPException(403, "Not your avatar")
    _creator.delete_avatar(avatar_id)
    return {"message": "Avatar deleted"}


@router.post("/{avatar_id}/generate", response_model=JobResponse)
async def generate_with_avatar(
    avatar_id: str,
    text: str = Form(None, description="Text to speak (uses TTS)"),
    audio: UploadFile = File(None, description="Audio file (alternative to text)"),
    voice: str = Form(None, description="Override voice preset"),
    prompt: str = Form(default="", description="Scene description"),
    max_duration: float = Form(
        default=0,
        ge=0,
        le=float(MAX_DURATION_SECONDS),
        description=MAX_DURATION_HELP,
    ),
    user: dict = Depends(get_current_user),
):
    """
    Generate video using a saved avatar.
    Just pick your avatar and type text — no need to upload image again!

    **Duration:** Uses your audio/TTS length; use **max_duration=0** for full length (capped by server — see `GET /health`).
    """
    avatar = _creator.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(404, "Avatar not found")

    image_path = avatar["image_path"]
    if not os.path.exists(image_path):
        raise HTTPException(404, "Avatar image file missing")

    # Determine audio source
    audio_path = None

    if audio and audio.filename:
        # User uploaded audio
        ext = Path(audio.filename).suffix.lower()
        audio_bytes = await audio.read()
        audio_path = str(_storage.save_upload(audio_bytes, ext))
        if ext != ".wav":
            wav = audio_path.rsplit(".", 1)[0] + ".wav"
            os.system(f"ffmpeg -i '{audio_path}' -ar 16000 -ac 1 '{wav}' -y -loglevel quiet")
            audio_path = wav

    elif text and text.strip():
        # Generate speech from text
        tts = TTSEngine(output_dir=str(_storage.temp_dir))
        # Use avatar's matched voice or override
        tts_voice = voice or avatar.get("voice_analysis", {}).get("matched_voice", "en-US-GuyNeural")
        audio_path = tts.generate(text=text, voice=tts_voice)

    else:
        raise HTTPException(400, "Provide either text or audio")

    # Create job
    from Backend.jobs.queue import Job
    job = _queue.create_job(
        image_path=image_path,
        audio_path=audio_path,
        prompt=prompt or f"A person speaking naturally",
        max_duration=max_duration,
        output_path="",
    )
    job.output_path = str(_storage.get_output_path(job.job_id))

    _worker.process_job(job)

    return JobResponse(
        job_id=job.job_id,
        status=JobStatus.QUEUED,
        message=f"Generating with avatar '{avatar['name']}'",
    )
