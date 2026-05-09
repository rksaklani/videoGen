"""
Avatar Studio API Server
Usage: python -m Backend.main
Docs:  http://localhost:8000/docs
"""
import os
import yaml
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Load .env file
env_path = Path("Backend/.env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

from Backend.utils.logger import setup_logger
from Backend.utils.storage import Storage
from Backend.utils.cleanup import FileCleanup
from Backend.core.engine import AvatarEngine
from Backend.jobs.queue import JobQueue
from Backend.jobs.worker import Worker
from Backend.api.routes import router as api_router, init_routes
from Backend.api.avatar_routes import router as avatar_router, init_avatar_routes
from Backend.api.template_routes import router as template_router
from Backend.auth.routes import router as auth_router
from Backend.billing.routes import router as billing_router
from Backend.db import mongodb

CONFIG_PATH = "Backend/config.yaml"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Avatar Studio server...")

    # Connect to MongoDB (optional — falls back to in-memory)
    mongo_uri = os.getenv("MONGODB_URI", app.state.config.get("database", {}).get("uri", "mongodb://localhost:27017"))
    mongo_db = os.getenv("MONGODB_NAME", app.state.config.get("database", {}).get("name", "avatar_studio"))
    await mongodb.connect(mongo_uri, mongo_db)

    # Load AI models
    app.state.engine.load_models()

    # Start file cleanup
    app.state.cleanup.start()

    logger.info("Server ready!")
    yield

    # Shutdown
    app.state.cleanup.stop()
    await mongodb.disconnect()
    logger.info("Server stopped.")


def create_app() -> FastAPI:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    setup_logger(level=config["logging"]["level"], log_file=config["logging"]["file"])

    app = FastAPI(
        title="Avatar Studio API",
        description="Generate audio-driven avatar videos with AI",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    cors_origins = config.get("cors", {}).get("origins", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if isinstance(cors_origins, list) else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    from Backend.api.rate_limit import limiter, rate_limit_handler
    from slowapi.errors import RateLimitExceeded
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    # Initialize components
    storage_cfg = config["storage"]
    storage = Storage(
        upload_dir=storage_cfg["upload_dir"],
        output_dir=storage_cfg["output_dir"],
        temp_dir=storage_cfg["temp_dir"],
    )

    engine = AvatarEngine(CONFIG_PATH)
    queue = JobQueue()
    worker = Worker(engine, queue)
    cleanup = FileCleanup(
        dirs=[storage_cfg["upload_dir"], storage_cfg["temp_dir"]],
        max_age_hours=24.0,
        interval_minutes=30.0,
    )

    # Store in app state for lifespan access
    app.state.config = config
    app.state.engine = engine
    app.state.cleanup = cleanup

    # Wire routes
    init_routes(engine, queue, worker, storage)
    init_avatar_routes(engine, queue, worker, storage)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(avatar_router, prefix="/api/v1")
    app.include_router(template_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(billing_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "name": "Avatar Studio API",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return app


app = create_app()

if __name__ == "__main__":
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    uvicorn.run(
        "Backend.main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        workers=config["server"]["workers"],
        reload=False,
    )
