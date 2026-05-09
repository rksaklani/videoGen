# Avatar API — Production Backend

Audio-driven avatar video generation API, powered by HunyuanVideo-Avatar.

## Structure

```
Backend/
├── main.py                  ← FastAPI entry point
├── config.yaml              ← All settings (no magic numbers)
├── requirements.txt         ← API-specific dependencies
│
├── engine/                  ← AI engine (HunyuanVideo-Avatar core)
│   ├── inference.py         ← Model loading
│   ├── sample_inference_audio.py  ← Main prediction
│   ├── config.py            ← Engine args
│   ├── constants.py         ← Model paths
│   ├── modules/             ← Transformer, attention, MLP
│   ├── diffusion/           ← Diffusion pipeline + scheduler
│   ├── vae/                 ← Video encoder/decoder
│   ├── data_kits/           ← Audio + face processing
│   └── text_encoder/        ← Text encoder utils
│
├── core/                    ← Production wrapper
│   ├── engine.py            ← Clean API around the AI engine
│   ├── preprocessor.py      ← Image/audio/video input handling
│   └── postprocessor.py     ← Video saving, stitching, merge
│
├── api/                     ← REST endpoints
│   ├── routes.py            ← All API routes
│   └── schemas.py           ← Request/response validation
│
├── jobs/                    ← Background processing
│   ├── queue.py             ← Job management
│   └── worker.py            ← Async job execution
│
├── utils/                   ← Utilities
│   ├── storage.py           ← File storage (S3-ready)
│   └── logger.py            ← Centralized logging
│
├── weights/ → symlink       ← Model weights (80GB)
└── assets/ → symlink        ← Sample test files
```

## Quick Start

```bash
conda activate HunyuanVideo-Avatar
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
export PYTHONPATH=./
python -m Backend.main
```

Open: http://localhost:8000/docs

## API Endpoints

- `POST /api/v1/generate` — Upload image + audio → job ID
- `GET  /api/v1/status/{job_id}` — Check progress
- `GET  /api/v1/download/{job_id}` — Download video
- `GET  /api/v1/jobs` — List all jobs
- `GET  /api/v1/health` — System status
