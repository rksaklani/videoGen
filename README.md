# videoGen — Backend + Frontend

Full-stack **audio-driven avatar / talking-head video** app: **`Backend`** (FastAPI API + diffusion inference + job queue) and **`Frontend`** (React 18 + Vite dashboard). Heavy models and pipelines live under **`Backend/engine/`** and **`Backend/core/`**.

| Area | Role | Docs |
|------|------|------|
| **Backend** | REST API, optional Mongo-backed jobs, GPU worker, FFmpeg, TTS | [`Backend/README.md`](Backend/README.md) |
| **Frontend** | Marketing site + dashboard (text/audio/video/dialogue/avatars) | [`Frontend/README.md`](Frontend/README.md) |

---

## Requirements (short)

- **Linux + NVIDIA GPU** recommended for inference (see project install notes / conda).
- **Python 3.10+**, **CUDA PyTorch**, **`ffmpeg`** on `PATH`.
- **Node.js 18+** for the Frontend (`npm ci`).

Download **model weights** into `Backend/weights/` (often tens of GB — see weight layout under that tree or your model source).

---

## One-command stack (recommended)

From the **repository root** (uses conda env **`VideoGen`** in `start.sh` — adjust `conda activate` if needed):

```bash
bash start.sh
```

| Service | URL |
|--------|-----|
| **Frontend** | http://localhost:3000 |
| **API docs** | http://localhost:8000/docs |
| **Health** | http://localhost:8000/api/v1/health |

Logs: `Backend/logs/server.log`, `Backend/logs/frontend.log` · Stop: `./stop.sh` or Ctrl+C in the `start.sh` terminal.

---

## Backend (manual)

```bash
export PYTHONPATH="$(pwd)"
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH}"   # if using conda
python -m Backend.main
```

| Item | Location |
|------|----------|
| **Config** | `Backend/config.yaml` (inference, storage, CORS) |
| **Dependencies** | `Backend/requirements.txt` — install **PyTorch CUDA** first where applicable |
| **Entry** | `python -m Backend.main` |

**Useful env (see `Backend/.env.example` if present):**

| Variable | Purpose |
|----------|---------|
| **`JWT_SECRET`** | Sign auth tokens (set in production) |
| **`MONGODB_URI`** / **`MONGODB_NAME`** | Durable **`jobs`** collection (optional; falls back to in-memory if unset/unreachable) |
| **`JOB_WORKER_MODE`** | **`embedded`** (API runs GPU worker in-process, default) or **`api_only`** (enqueue only; run `python -m Backend.worker_main` on a GPU machine) |
| **`JOB_QUEUE_MEMORY_ONLY`** | `1` forces in-memory queue (no Mongo persistence) |

Open **`http://localhost:8000/docs`** for OpenAPI. **`GET /api/v1/health`** exposes GPU status, **`generation_limits`**, and **`worker_mode`**.

---

## Frontend (manual)

```bash
cd Frontend
cp .env.example .env          # optional; defaults work if API is localhost:8000
npm ci
npm run dev
```

| Variable | Purpose |
|----------|---------|
| **`VITE_API_URL`** | Backend origin **without** `/api/v1` (e.g. `http://localhost:8000`) |
| **`VITE_APP_NAME`** | UI label (default can be **`videoGen`**) |

`cors.origins` in **`Backend/config.yaml`** must include the Frontend origin (e.g. `http://localhost:3000`). Production bundle: **`npm run build`** → **`Frontend/dist/`**.

---

## Project layout

```
.
├── Backend/
│   ├── main.py               # FastAPI app
│   ├── worker_main.py        # Standalone GPU worker (with api_only + Mongo)
│   ├── config.yaml
│   ├── requirements.txt
│   ├── api/                  # Routes, schemas, limits
│   ├── core/                 # AvatarEngine, preprocess, TTS, etc.
│   ├── jobs/                 # Job queue + embedded worker
│   ├── db/                   # Mongo (Motor + sync helpers for jobs)
│   └── engine/               # Diffusion / VAE stack
├── Frontend/
│   ├── src/                  # React app, RTK Query API layer
│   ├── package.json
│   └── .env.example
├── Dockerfile
├── docker-compose.yml
├── environment.yml
├── scripts/
├── start.sh / stop.sh
└── README.md
```

---
