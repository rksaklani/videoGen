# Avatar Studio — Backend (API + inference)

FastAPI service wrapping the diffusion **audio → video** pipeline. For **install, PyTorch CUDA, Docker, and weights**, see the repo root **`README.md`** and **`docs/INSTALL.md`**.

---

## Structure

```
Backend/
├── main.py                   # FastAPI entry (uvicorn: python -m Backend.main)
├── config.yaml               # Server, model paths, inference, storage
├── requirements.txt          # Pip deps — install PyTorch separately (see INSTALL)
├── api/                      # Routes, schemas, limits
├── core/                     # AvatarEngine, preprocess, postprocess, dialogue, TTS
├── engine/                   # Diffusion/VAE/transformer (research stack)
├── jobs/                     # In-memory worker + queue
├── weights/                  # Checkpoints (not in git — symlink or copy)
├── data/                     # uploads, outputs, temp (runtime)
└── logs/
```

---

## Quick start

From **repository root** (parent of `Backend/`):

```bash
export PYTHONPATH="$(pwd)"
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH}"   # if conda
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r Backend/requirements.txt
python -m Backend.main
```

- **Swagger:** http://localhost:8000/docs  
- **Health:** http://localhost:8000/api/v1/health  

---

## Notable endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | **`/api/v1/generate`** | Image/audio (or video) → job ID |
| POST | **`/api/v1/generate-from-text`** | Image + script (TTS) → job ID |
| GET | **`/api/v1/status/{job_id}`** | Progress |
| GET | **`/api/v1/download/{job_id}`** | MP4 when complete |
| GET | **`/api/v1/health`** | GPU + **`generation_limits`** |

Full list in **`openapi.json`** via **`/docs`**.
