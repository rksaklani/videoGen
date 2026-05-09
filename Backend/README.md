# videoGen — Backend (API + inference)

FastAPI service for the **audio / text → avatar video** pipeline (Hunyuan-based stack under **`engine/`**). The **Frontend** consumes this API via **`VITE_API_URL`**.

Install, PyTorch/CUDA, Docker, and weights: repo root **`README.md`** plus any **`docs/INSTALL.md`** in your clone.

---

## Layout

```
Backend/
├── main.py              # FastAPI (uvicorn: python -m Backend.main)
├── worker_main.py       # Standalone GPU poller when JOB_WORKER_MODE=api_only + Mongo
├── config.yaml           # Server, models, inference, storage, CORS
├── requirements.txt       # Pip (install PyTorch separately per INSTALL)
├── api/                   # Routes, schemas, rate limits
├── core/                  # AvatarEngine, preprocess, postprocess, dialogue, TTS
├── jobs/                   # JobQueue (Mongo optional), Worker, api_only runner
├── db/                     # Motor + sync Mongo helpers for job persistence
├── engine/                # Diffusion/VAE/transformer stack
├── weights/               # Checkpoints (not in git)
├── data/                  # uploads, outputs, temp
└── logs/
```

---

## Quick start

From **repository root**:

```bash
export PYTHONPATH="$(pwd)"
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH}"   # if conda
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r Backend/requirements.txt
python -m Backend.main
```

- **Swagger:** http://localhost:8000/docs  
- **Health:** http://localhost:8000/api/v1/health (`generation_limits`, `worker_mode`, GPU stats)

---

## Jobs & scaling

| Mode | When |
|------|------|
| **Embedded worker** | Default **`JOB_WORKER_MODE=embedded`**: GPU jobs run in the API process after **`load_models()`**. |
| **API-only + worker** | **`JOB_WORKER_MODE=api_only`**: API enqueues durable jobs to Mongo **`jobs`**; run **`python -m Backend.worker_main`** on the GPU host (same **`MONGODB_URI`**). |
| **In-memory queue** | **`JOB_QUEUE_MEMORY_ONLY=1`**: no Mongo; jobs lost on restart. |

After a restart with Mongo, stale **`processing`** jobs are reset to **`queued`**; embedded mode **replays** queued work into the local **`Worker`**.

---

## Notable HTTP routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | **`/api/v1/generate`** | Image/audio or video → job ID |
| POST | **`/api/v1/generate-from-text`** | Image + TTS script → job ID |
| POST | **`/api/v1/video-reference`** | Reference video flows → job ID |
| GET | **`/api/v1/status/{job_id}`** | Progress |
| GET | **`/api/v1/download/{job_id}`** | MP4 when complete |
| GET | **`/api/v1/health`** | Readiness, limits, **`worker_mode`** |

Avatars: **`/api/v1/avatars/...`** · Full list in **`/docs`**.
