"""API request/response models."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
    worker_mode: str = Field(default="embedded", description="embedded | api_only")
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

