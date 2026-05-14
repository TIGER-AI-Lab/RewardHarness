#!/bin/bash
# Kill vLLM processes safely without affecting parent
trap '' TERM HUP
for pid in $(pgrep -f "vllm.entrypoints" 2>/dev/null); do
    kill -9 "$pid" 2>/dev/null || true
done
sleep 2
remaining=$(pgrep -c -f "vllm.entrypoints" 2>/dev/null || echo 0)
echo "vllm processes remaining: $remaining"
