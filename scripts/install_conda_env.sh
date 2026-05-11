#!/usr/bin/env bash
# Install Python (PyTorch + Backend/requirements.txt) and Frontend (npm) into a conda env.
# Usage (from repo root):
#   bash scripts/install_conda_env.sh
#   VIDEOGEN_CONDA_ENV=HunyuanVideo-Avatar bash scripts/install_conda_env.sh
#
# PyTorch: install CUDA 12.4 wheels by default; set TORCH_INDEX_URL to override, e.g. CPU-only:
#   TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu bash scripts/install_conda_env.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

CONDA_ENV="${VIDEOGEN_CONDA_ENV:-VideoGen}"
TORCH_INDEX_URL="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu124}"

if [[ ! -f "$(conda info --base 2>/dev/null)/etc/profile.d/conda.sh" ]]; then
  echo "conda not found. Install Miniconda/Anaconda and try again."
  exit 1
fi
# shellcheck source=/dev/null
source "$(conda info --base)/etc/profile.d/conda.sh"

ENV_DIR="$(conda info --base)/envs/${CONDA_ENV}"
if [[ ! -d "$ENV_DIR" ]]; then
  echo "Conda env '${CONDA_ENV}' not found. Create it first, e.g.:"
  echo "  conda create -n ${CONDA_ENV} python=3.10 -y"
  echo "  conda activate ${CONDA_ENV}"
  exit 1
fi

conda activate "${CONDA_ENV}"
echo "Using conda env: ${CONDA_ENV} ($(command -v python))"

echo ""
echo "==> PyTorch (torch, torchvision, torchaudio) from ${TORCH_INDEX_URL}"
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url "${TORCH_INDEX_URL}"

echo ""
echo "==> Backend/requirements.txt"
pip install -r Backend/requirements.txt

echo ""
echo "==> Frontend (npm ci)"
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not on PATH. Install Node.js 18+ (e.g. nvm or system package)."
  exit 1
fi
npm ci --prefix Frontend

echo ""
echo "Done. Activate with: conda activate ${CONDA_ENV}"
echo "Run stack: bash start.sh"
