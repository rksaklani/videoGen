"""FastAPI dependencies shared across routers."""
from __future__ import annotations

from fastapi import HTTPException, Request, status


def require_embedded_inference_ready(request: Request) -> None:
    """
    Use on routes that run diffusion / preprocessor / optimisation on THIS process.

    When ``JOB_WORKER_MODE=api_only``, models are not loaded here — callers should
    use enqueue-only endpoints or a host running ``JOB_WORKER_MODE=embedded``.
    """
    mode = getattr(request.app.state, "job_worker_mode", "embedded")
    if mode == "api_only":
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "This endpoint needs a loaded inference engine on the API process. "
                "Use JOB_WORKER_MODE=embedded on this server, "
                "or POST generation jobs and run python -m Backend.worker_main elsewhere."
            ),
        )
    eng = getattr(request.app.state, "engine", None)
    if eng is None or not eng.get_status().get("loaded"):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference engine is not ready yet. Retry shortly.",
        )
