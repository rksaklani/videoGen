# Avatar Studio — Backend + Frontend

Full-stack **audio-driven avatar video** app: **FastAPI** (`Backend`) + **React/Vite** (`Frontend`). Core generation uses the HunyuanVideo-Avatar–style diffusion stack under `Backend/engine/`.

| Area | Role | Docs |
|------|------|------|
| **Backend** | REST API, job queue, model inference, FFmpeg | [`Backend/README.md`](Backend/README.md) · full install **[`docs/INSTALL.md`](docs/INSTALL.md)** |
| **Frontend** | Dashboard UI (text/audio/video/dialogue flows) | [`Frontend/README.md`](Frontend/README.md) |

---

## Requirements (short)

- **Linux + NVIDIA GPU** recommended for inference (see **`docs/INSTALL.md`**).
- **Python 3.10**, **CUDA PyTorch**, **`ffmpeg`** on `PATH`.
- **Node.js 18+** for the Frontend (use **`npm ci`**).

Download **model weights** into `Backend/weights/` (see `Backend/weights/` or Hugging Face — often ~tens of GB).

---

## One-command stack (recommended)

From the **repository root** (requires conda env **`VideoGen`** per `start.sh`, or edit `conda activate`):

```bash
bash start.sh
```

- **Frontend:** http://localhost:3000  
- **API docs:** http://localhost:8000/docs  
- **Health:** http://localhost:8000/api/v1/health  

Logs: `Backend/logs/server.log`, `Backend/logs/frontend.log` · Stop: `./stop.sh` or Ctrl+C in the `start.sh` terminal.

---

## Backend (manual)

```bash
export PYTHONPATH="$(pwd)"
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH}"   # if using conda
python -m Backend.main
```

Configuration: **`Backend/config.yaml`** · Dependencies: **`Backend/requirements.txt`** (install PyTorch CUDA **first** — **`docs/INSTALL.md`**).

Entry point: **`python -m Backend.main`** · Open **`/docs`** for OpenAPI.

---

## Frontend (manual)

```bash
cd Frontend
cp .env.example .env          # optional; defaults work if API is localhost:8000
npm ci
npm run dev
```

- **`VITE_API_URL`** — Base URL **without** `/api/v1` (example: `http://localhost:8000`). Same origin as CORS entries in **`Backend/config.yaml`**.
- Production build: **`npm run build`** → **`Frontend/dist/`**.

---

## Project layout

```
.
├── Backend/                 # FastAPI + inference engine
│   ├── main.py
│   ├── config.yaml
│   ├── requirements.txt
│   └── engine/              # diffusion, VAE, audio pipeline
├── Frontend/                # Vite + React dashboard
│   ├── src/
│   ├── package.json
│   └── .env.example
├── docs/INSTALL.md          # PyTorch, conda, Docker
├── Dockerfile
├── docker-compose.yml
├── environment.yml
├── scripts/check_system.sh
├── start.sh / stop.sh
└── README.md                  # ← this file
```

---




