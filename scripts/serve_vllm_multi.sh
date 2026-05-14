#!/usr/bin/env bash
# serve_vllm_multi.sh — Start multiple vLLM endpoints for Qwen2.5-VL-7B-Instruct
# Default: 4 GPUs × 2 endpoints per GPU = 8 endpoints (ports 8000-8007)
# L40S (46GB): 0.45 per endpoint × 2 = 90% per GPU
set -euo pipefail

# Clean broken /cvmfs paths from environment (Compute Canada module system issue)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/cm/shared/apps/slurm/current/bin"
export CPATH="/cm/shared/apps/slurm/current/include"
export LIBRARY_PATH="/cm/shared/apps/slurm/current/lib64/slurm:/cm/shared/apps/slurm/current/lib64"
export LD_LIBRARY_PATH="/cm/local/apps/cuda/libs/current/lib64:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
unset BASH_ENV

# Model path — update to match your local snapshot
MODEL="${VLLM_MODEL_PATH:-Qwen/Qwen2.5-VL-7B-Instruct}"
PYTHON="${VLLM_PYTHON:-python}"
NUM_GPUS="${NUM_GPUS:-4}"
ENDPOINTS_PER_GPU="${ENDPOINTS_PER_GPU:-1}"
BASE_PORT="${BASE_PORT:-8000}"
GPU_MEM="${GPU_MEM:-0.85}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-16384}"

echo "Starting vLLM endpoints..."
echo "Model: $MODEL"
echo "GPUs: $NUM_GPUS, Endpoints/GPU: $ENDPOINTS_PER_GPU"
echo "Ports: $BASE_PORT - $((BASE_PORT + NUM_GPUS * ENDPOINTS_PER_GPU - 1))"

PIDS=()

cleanup() {
    echo "Shutting down all vLLM endpoints..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait
    echo "All endpoints stopped."
}
trap cleanup EXIT INT TERM

TOTAL=$((NUM_GPUS * ENDPOINTS_PER_GPU))
for i in $(seq 0 $((TOTAL - 1))); do
    GPU=$((i / ENDPOINTS_PER_GPU))
    PORT=$((BASE_PORT + i))
    echo "Starting endpoint on GPU $GPU, port $PORT..."
    CUDA_VISIBLE_DEVICES=$GPU $PYTHON -m vllm.entrypoints.openai.api_server \
        --model "$MODEL" \
        --served-model-name Qwen2.5-VL-7B-Instruct \
        --tensor-parallel-size 1 \
        --port "$PORT" \
        --max-model-len "$MAX_MODEL_LEN" \
        --limit-mm-per-prompt '{"image": 5}' \
        --dtype bfloat16 \
        --gpu-memory-utilization "$GPU_MEM" &
    PIDS+=($!)
done

echo "All $TOTAL endpoints starting. Waiting for them to be ready..."
echo "PIDs: ${PIDS[*]}"
wait
