"""
Standalone GPU worker for videoGen: pulls ``queued`` jobs from MongoDB and runs AvatarEngine.

Requires ``MONGODB_URI`` + matching ``JOB_QUEUE_*`` defaults as used by the API.
Do not run embedded generation on the API while this worker is claiming the same queue.

Usage (from repo root, PYTHONPATH set):
    export MONGODB_URI=mongodb://localhost:27017
    python -m Backend.worker_main
"""
from __future__ import annotations

import os
import time

import yaml
from loguru import logger

from Backend.env_load import load_application_env

load_application_env()

from Backend.utils.logger import setup_logger
from Backend.core.engine import AvatarEngine
from Backend.jobs.queue import JobQueue
from Backend.jobs.worker import Worker
from Backend.db.mongo_sync import open_jobs_collection

CONFIG_PATH = "Backend/config.yaml"


def main():
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    setup_logger(level=config["logging"]["level"], log_file=config["logging"]["file"])

    mongo_uri = (os.getenv("MONGODB_URI") or "").strip() or config.get("database", {}).get("uri") or "mongodb://localhost:27017"
    mongo_db = (os.getenv("MONGODB_NAME") or "").strip() or config.get("database", {}).get("name") or "avatar_studio"

    poll = float(os.getenv("WORKER_POLL_INTERVAL", "1.0"))
    jobs_coll = open_jobs_collection(mongo_uri, mongo_db)
    if jobs_coll is None:
        logger.error("Standalone worker requires a reachable MongoDB (MONGODB_URI). Aborting.")
        raise SystemExit(1)

    queue = JobQueue(jobs_coll)
    queue.hydrate()

    engine = AvatarEngine(CONFIG_PATH)
    logger.info("Loading models for standalone worker...")
    engine.load_models()
    worker_impl = Worker(engine, queue)

    logger.info(
        "Worker loop started uri=%s db=%s poll=%ss",
        mongo_uri.split("@")[-1] if "@" in mongo_uri else mongo_uri,
        mongo_db,
        poll,
    )
    while True:
        job = queue.claim_next_queued_job()
        if job:
            worker_impl.process_job(job)
        else:
            time.sleep(poll)


if __name__ == "__main__":
    main()
