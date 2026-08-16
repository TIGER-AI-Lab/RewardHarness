#!/usr/bin/env bash
# Slurm wrapper that brings up 4 vLLM endpoints on one node and writes a
# hostname:port pointer file. Edit the #SBATCH lines and the env-var
# defaults below for your cluster before submitting.
#
#SBATCH --account=your-slurm-account
#SBATCH --gres=gpu:l40s:4
#SBATCH --time=8:00:00
#SBATCH --job-name=vllm-rh
#SBATCH --cpus-per-gpu=16
#SBATCH --mem=500G
#SBATCH --output=/tmp/vllm-slurm-%j.log
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

# Override these with `export VAR=… ; sbatch scripts/sbatch_vllm.sh`
# RH_ROOT must be set to your RewardHarness checkout (no default — fail fast
# if missing so users can't accidentally run the template paths).
RH_ROOT="${RH_ROOT:?Set RH_ROOT=/abs/path/to/your/reward-harness-checkout before sbatch}"
PYTHON="${VLLM_PYTHON:-$RH_ROOT/.venv/bin/python}"
MODEL="${VLLM_MODEL_PATH:-Qwen/Qwen2.5-VL-7B-Instruct}"
NUM_GPUS="${NUM_GPUS:-4}"
BASE_PORT="${BASE_PORT:-8000}"
GPU_MEM="${GPU_MEM:-0.85}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-16384}"

HOSTNAME_DIR="${SLURM_NODES_DIR:-$RH_ROOT/results/slurm_nodes}"
mkdir -p "$HOSTNAME_DIR"
HOSTNAME_FILE="$HOSTNAME_DIR/slurm_node_${SLURM_JOB_ID}.txt"
echo "$(hostname):${BASE_PORT}" > "$HOSTNAME_FILE"
echo "Node $(hostname) ready, job $SLURM_JOB_ID, ports ${BASE_PORT}-$((BASE_PORT+NUM_GPUS-1))"

PIDS=()
for ((GPU=0; GPU<NUM_GPUS; GPU++)); do
    PORT=$((BASE_PORT + GPU))
    echo "Starting GPU $GPU on port $PORT..."
    CUDA_VISIBLE_DEVICES=$GPU $PYTHON -m vllm.entrypoints.openai.api_server \
        --model "$MODEL" \
        --served-model-name Qwen2.5-VL-7B-Instruct \
        --tensor-parallel-size 1 \
        --port $PORT \
        --max-model-len "$MAX_MODEL_LEN" \
        --limit-mm-per-prompt '{"image": 5}' \
        --dtype bfloat16 \
        --gpu-memory-utilization "$GPU_MEM" &
    PIDS+=($!)
done

echo "All $NUM_GPUS endpoints starting. PIDs: ${PIDS[*]}"
wait
