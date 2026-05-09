"""Database models for jobs, avatars, and users."""
from datetime import datetime
from typing import Optional


def job_doc(job_id: str, user_id: str, image_path: str, audio_path: str,
            prompt: str, max_duration: float, output_path: str) -> dict:
    return {
        "job_id": job_id,
        "user_id": user_id,
        "image_path": image_path,
        "audio_path": audio_path,
        "prompt": prompt,
        "max_duration": max_duration,
        "output_path": output_path,
        "status": "queued",
        "progress": 0.0,
        "message": "Queued",
        "result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "completed_at": None,
    }


def avatar_doc(user_id: str, name: str, image_path: str,
               voice_preset: str = "en-male", default_prompt: str = "",
               voice_clone_path: str = None) -> dict:
    return {
        "user_id": user_id,
        "name": name,
        "image_path": image_path,
        "voice_preset": voice_preset,
        "voice_clone_path": voice_clone_path,
        "default_prompt": default_prompt,
        "created_at": datetime.utcnow(),
    }


def user_doc(email: str, name: str, hashed_password: str) -> dict:
    return {
        "email": email,
        "name": name,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "generation_count": 0,
    }
