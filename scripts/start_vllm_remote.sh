#!/bin/bash
# start_vllm_remote.sh — Boot a single vLLM endpoint on an assigned GPU.
# Intended to be invoked over SSH against a remote node (or by a Slurm task)
# with $PORT, $GPU_MEM, and $GPU_ID set. Pins the Slurm + CUDA paths so the
# python venv resolves its native deps correctly even when called from a
# non-login shell.
#
# The default paths below match a Bright Cluster Manager install (the
# `/cm/...` layout). On a different cluster, override via:
#
#     SLURM_PREFIX=/opt/slurm \
#     CUDA_LIBS=/usr/local/cuda/lib64 \
#     bash scripts/start_vllm_remote.sh <PORT> <GPU_MEM> <GPU_ID>
#
# or set them once at the top of your sbatch wrapper.

SLURM_PREFIX="${SLURM_PREFIX:-/cm/shared/apps/slurm/current}"
CUDA_LIBS="${CUDA_LIBS:-/cm/local/apps/cuda/libs/current/lib64}"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${SLURM_PREFIX}/bin"
export CPATH="${SLURM_PREFIX}/include"
export LIBRARY_PATH="${SLURM_PREFIX}/lib64/slurm:${SLURM_PREFIX}/lib64"
export LD_LIBRARY_PATH="${CUDA_LIBS}:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
unset BASH_ENV

PORT=$1
GPU_MEM=$2
GPU_ID=${3:-0}

echo "Starting vLLM on $(hostname) GPU=$GPU_ID port=$PORT gpu_mem=$GPU_MEM at $(date)"
CUDA_VISIBLE_DEVICES=$GPU_ID python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-VL-7B-Instruct \
    --served-model-name Qwen2.5-VL-7B-Instruct \
    --tensor-parallel-size 1 \
    --port $PORT \
    --max-model-len 16384 \
    --limit-mm-per-prompt '{"image": 5}' \
    --dtype bfloat16 \
    --gpu-memory-utilization $GPU_MEM
