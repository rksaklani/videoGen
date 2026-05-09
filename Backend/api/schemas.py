"""API request/response models."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

from Backend.api.limits import MAX_DURATION_SECONDS


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateRequest(BaseModel):
    prompt: str = Field(default="", description="Scene description")
    max_duration: float = Field(
        default=5.0,
        ge=1.0,
        le=float(MAX_DURATION_SECONDS),
        description=f"Max output seconds (cap {MAX_DURATION_SECONDS}s, same as server config).",
    )
    seed: int = Field(default=42, description="Random seed for reproducibility")
    steps: int = Field(default=30, ge=10, le=50, description="Inference steps")
    cfg_scale: float = Field(default=6.5, ge=1.0, le=15.0, description="Guidance scale")


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = 0.0
    message: str = ""
    result: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    engine_loaded: bool
    gpu: dict
    generation_limits: dict = Field(
        default_factory=dict,
        description="Server caps for video length and chunking (from config.yaml).",
    )


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: str = Field(default="en-male", description="Voice preset or full voice name")
    rate: str = Field(default="+0%", description="Speed: e.g. '+10%', '-20%'")
    pitch: str = Field(default="+0Hz", description="Pitch: e.g. '+5Hz', '-10Hz'")


class VoiceInfo(BaseModel):
    key: str
    voice_name: str
    language: str
