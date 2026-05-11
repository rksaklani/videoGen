"""
videoGen API server
Usage: python -m Backend.main
Docs:  http://localhost:8000/docs
"""
from Backend.env_load import load_application_env

load_application_env()

import os
import yaml
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from Backend.utils.logger import setup_logger
from Backend.utils.storage import Storage
from Backend.utils.cleanup import FileCleanup
from Backend.core.engine import AvatarEngine
from Backend.jobs.queue import JobQueue
from Backend.jobs.worker import Worker, ApiOnlyJobRunner
from Backend.api.routes import router as api_router, init_routes
from Backend.api.avatar_routes import router as avatar_router, init_avatar_routes
from Backend.api.template_routes import router as template_router
from Backend.auth.routes import router as auth_router
from Backend.billing.routes import router as billing_router
from Backend.db import mongodb
from Backend.db.mongo_sync import open_jobs_collection

CONFIG_PATH = "Backend/config.yaml"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting videoGen server...")

    mongo_uri = app.state.mongo_uri
    mongo_db = app.state.mongo_db_name
    await mongodb.connect(mongo_uri, mongo_db)

    app.state.queue.hydrate()

    if app.state.job_worker_mode != "api_only":
        app.state.engine.load_models()
        if isinstance(app.state.job_runner, Worker):
            app.state.queue.replay_queued_to_worker(app.state.job_runner.process_job)
    else:
        logger.info("JOB_WORKER_MODE=api_only — GPU models not loaded on this process")

    app.state.cleanup.start()

    logger.info("Server ready!")
    yield

    app.state.cleanup.stop()
    await mongodb.disconnect()
    logger.info("Server stopped.")


def create_app() -> FastAPI:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    setup_logger(level=config["logging"]["level"], log_file=config["logging"]["file"])

    env_name = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "").strip().lower()
    if env_name in ("production", "prod"):
        if not (os.getenv("JWT_SECRET") or "").strip():
            raise RuntimeError(
                "JWT_SECRET must be set when ENVIRONMENT or APP_ENV is production."
            )

    mongo_uri = (os.getenv("MONGODB_URI") or "").strip() or config.get("database", {}).get("uri") or "mongodb://localhost:27017"
    mongo_db = (os.getenv("MONGODB_NAME") or "").strip() or config.get("database", {}).get("name") or "avatar_studio"

    job_worker_mode = (os.getenv("JOB_WORKER_MODE") or "embedded").strip().lower()
    if job_worker_mode not in ("embedded", "api_only"):
        logger.warning("JOB_WORKER_MODE must be 'embedded' or 'api_only'; got %r — using embedded", job_worker_mode)
        job_worker_mode = "embedded"

    jobs_coll = None
    if os.getenv("JOB_QUEUE_MEMORY_ONLY", "").lower() in ("1", "true", "yes"):
        logger.info("JOB_QUEUE_MEMORY_ONLY set — Mongo job persistence disabled")
    else:
        jobs_coll = open_jobs_collection(mongo_uri, mongo_db)
        if jobs_coll is not None:
            logger.info("Job queue using MongoDB collection {}.jobs", mongo_db)

    app = FastAPI(
        title="videoGen API",
        description="Generate audio-driven avatar videos with AI",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    cors_origins = config.get("cors", {}).get("origins", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if isinstance(cors_origins, list) else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from Backend.api.rate_limit import limiter, rate_limit_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    storage_cfg = config["storage"]
    storage = Storage(
        upload_dir=storage_cfg["upload_dir"],
        output_dir=storage_cfg["output_dir"],
        temp_dir=storage_cfg["temp_dir"],
    )

    engine = AvatarEngine(CONFIG_PATH)
    queue = JobQueue(jobs_coll)
    worker = ApiOnlyJobRunner() if job_worker_mode == "api_only" else Worker(engine, queue)
    cleanup = FileCleanup(
        dirs=[storage_cfg["upload_dir"], storage_cfg["temp_dir"]],
        max_age_hours=24.0,
        interval_minutes=30.0,
    )

    upload_mb_env = (os.getenv("MAX_UPLOAD_SIZE_MB") or "").strip()
    if upload_mb_env:
        max_upload_bytes = int(float(upload_mb_env) * 1024 * 1024)
    else:
        max_upload_bytes = int(float(storage_cfg.get("max_upload_size_mb", 100)) * 1024 * 1024)

    app.state.config = config
    app.state.engine = engine
    app.state.cleanup = cleanup
    app.state.queue = queue
    app.state.mongo_uri = mongo_uri
    app.state.mongo_db_name = mongo_db
    app.state.job_worker_mode = job_worker_mode
    app.state.job_runner = worker

    init_routes(
        engine,
        queue,
        worker,
        storage,
        job_worker_mode=job_worker_mode,
        max_upload_bytes=max_upload_bytes,
    )
    init_avatar_routes(engine, queue, worker, storage, max_upload_bytes=max_upload_bytes)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(avatar_router, prefix="/api/v1")
    app.include_router(template_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(billing_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "name": "videoGen API",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return app


app = create_app()


if __name__ == "__main__":
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    srv = config.get("server", {})
    host = (os.getenv("SERVER_HOST") or os.getenv("HOST") or srv.get("host") or "0.0.0.0").strip()
    port = int(os.getenv("SERVER_PORT") or os.getenv("PORT") or srv.get("port") or 8000)
    workers = int(os.getenv("UVICORN_WORKERS") or srv.get("workers") or 1)

    uvicorn.run(
        "Backend.main:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
    )
