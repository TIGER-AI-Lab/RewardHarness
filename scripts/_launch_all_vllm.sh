#!/usr/bin/env bash
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
# Launch one vLLM instance per GPU and keep the script alive.
# Respects the same env-var conventions as scripts/serve_vllm_multi.sh:
#   NUM_GPUS    (default 4)         — how many GPUs to bind
#   BASE_PORT   (default 8000)      — first port; later GPUs get +1, +2, …
#   GPU_MEM     (default 0.85)      — fraction passed to --gpu-memory-utilization
trap '' TERM HUP

SCRIPT_DIR="$(dirname "$0")"
NUM_GPUS="${NUM_GPUS:-4}"
BASE_PORT="${BASE_PORT:-8000}"
GPU_MEM="${GPU_MEM:-0.85}"

for ((gpu=0; gpu<NUM_GPUS; gpu++)); do
    port=$((BASE_PORT + gpu))
    echo "Launching vLLM on GPU $gpu, port $port (gpu_mem=$GPU_MEM)..."
    nohup "$SCRIPT_DIR/start_vllm_remote.sh" "$port" "$GPU_MEM" "$gpu" > "/tmp/vllm_gpu${gpu}.log" 2>&1 &
    echo "PID: $!"
done

echo "All $NUM_GPUS vLLM instances launched. Waiting for them..."
wait
echo "All vLLM processes exited."
