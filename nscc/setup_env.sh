#!/usr/bin/env bash
set -euo pipefail

# Run this once, interactively, on an NSCC ASPIRE2A compute node — not the
# login node. flash-attn's build step is heavy and login nodes kill
# long/CPU-heavy work. Grab a node first:
#   qsub -I -P csyuchen -q ai -l select=1:ncpus=5:ngpus=1 -l walltime=02:00:00

module load miniforge3

SCRATCH_ROOT="${HOME}/scratch"  # shared root across all your NSCC projects, not just this one
ENV_DIR="${SCRATCH_ROOT}/envs/medvlm-r1"

if [ ! -d "${ENV_DIR}" ]; then
  conda create -y -p "${ENV_DIR}" python=3.11
else
  echo "Env already exists at ${ENV_DIR}, skipping creation (safe to re-run after a partial failure)."
fi
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${ENV_DIR}"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_DIR}/src/open-r1-multimodal"
pip install -e ".[dev]"

# Matches upstream setup.sh, unmodified:
pip install wandb==0.18.3
pip install tensorboardx
pip install qwen_vl_utils torchvision
pip install flash-attn --no-build-isolation
pip install git+https://github.com/huggingface/transformers.git  # needed for correct deepspeed support

echo "Env created at ${ENV_DIR}"
echo "Activate later with: conda activate ${ENV_DIR}"
