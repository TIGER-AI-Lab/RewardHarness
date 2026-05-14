#!/bin/bash
# Launch 4 vLLM instances (one per GPU) and keep the script alive
trap '' TERM HUP

SCRIPT_DIR="$(dirname "$0")"

for gpu in 0 1 2 3; do
    port=$((8000 + gpu))
    echo "Launching vLLM on GPU $gpu, port $port..."
    nohup "$SCRIPT_DIR/start_vllm_remote.sh" "$port" 0.85 "$gpu" > "/tmp/vllm_gpu${gpu}.log" 2>&1 &
    echo "PID: $!"
done

echo "All 4 vLLM instances launched. Waiting for them..."
wait
echo "All vLLM processes exited."
