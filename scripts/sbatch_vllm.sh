#!/usr/bin/env bash
#SBATCH --account=your-slurm-account
#SBATCH --gres=gpu:l40s:4
#SBATCH --time=8:00:00
#SBATCH --job-name=vllm-rc
#SBATCH --cpus-per-gpu=16
#SBATCH --mem=500G
#SBATCH --output=/tmp/vllm-slurm-%j.log
set -euo pipefail

MODEL="Qwen/Qwen2.5-VL-7B-Instruct"
PYTHON="/path/to/your/reward-harness-checkout/.venv/bin/python"
BASE_PORT="${BASE_PORT:-8000}"

HOSTNAME_FILE="/path/to/your/reward-harness-checkout/results/gemini_v7/slurm_node_${SLURM_JOB_ID}.txt"
echo "$(hostname):${BASE_PORT}" > "$HOSTNAME_FILE"
echo "Node $(hostname) ready, job $SLURM_JOB_ID, ports ${BASE_PORT}-$((BASE_PORT+3))"

PIDS=()
for GPU in 0 1 2 3; do
    PORT=$((BASE_PORT + GPU))
    echo "Starting GPU $GPU on port $PORT..."
    CUDA_VISIBLE_DEVICES=$GPU $PYTHON -m vllm.entrypoints.openai.api_server \
        --model "$MODEL" \
        --served-model-name Qwen2.5-VL-7B-Instruct \
        --tensor-parallel-size 1 \
        --port $PORT \
        --max-model-len 16384 \
        --limit-mm-per-prompt '{"image": 5}' \
        --dtype bfloat16 \
        --gpu-memory-utilization 0.85 &
    PIDS+=($!)
done

echo "All 4 endpoints starting. PIDs: ${PIDS[*]}"
wait
