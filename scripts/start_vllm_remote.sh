#!/bin/bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/cm/shared/apps/slurm/current/bin"
export CPATH="/cm/shared/apps/slurm/current/include"
export LIBRARY_PATH="/cm/shared/apps/slurm/current/lib64/slurm:/cm/shared/apps/slurm/current/lib64"
export LD_LIBRARY_PATH="/cm/local/apps/cuda/libs/current/lib64:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
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
