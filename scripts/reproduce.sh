#!/usr/bin/env bash
# reproduce.sh — End-to-end reproducibility script for RewardHarness
# Runs setup → download → serve → evolution → benchmark → print results
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

VLLM_PIDS=()

cleanup() {
    echo ""
    echo "[cleanup] Shutting down vLLM endpoints..."
    for pid in "${VLLM_PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    # Kill any remaining vLLM processes on ports 8000-8015
    for port in $(seq 8000 8015); do
        fuser -k "$port/tcp" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    echo "[cleanup] Done."
}
trap cleanup EXIT INT TERM

timestamp() { date "+%Y-%m-%d %H:%M:%S"; }

echo "=================================================="
echo "RewardHarness End-to-End Reproduction"
echo "Started: $(timestamp)"
echo "=================================================="

# Step 1: Environment setup
echo ""
echo "[$(timestamp)] Step 1/7: Environment setup..."
bash scripts/setup_env.sh
echo "[$(timestamp)] Step 1 complete."

# Step 2: Download data
echo ""
echo "[$(timestamp)] Step 2/7: Downloading datasets..."
bash scripts/download_data.sh
echo "[$(timestamp)] Step 2 complete."

# Step 3: Start vLLM endpoints
echo ""
echo "[$(timestamp)] Step 3/7: Starting vLLM endpoints..."
bash scripts/serve_vllm_multi.sh &
VLLM_PIDS+=($!)
echo "[$(timestamp)] vLLM starting in background (PID: ${VLLM_PIDS[-1]})"

# Step 4: Wait for all endpoints to be healthy
echo ""
echo "[$(timestamp)] Step 4/7: Waiting for endpoints to be ready..."
PER_PORT_MAX_WAIT=600  # 10 minutes per port (vLLM cold start can be slow)
for port in $(seq 8000 8015); do
    echo -n "  Waiting for port $port..."
    waited=0
    until curl -sf "http://localhost:$port/v1/models" > /dev/null 2>&1; do
        sleep 5
        waited=$((waited + 5))
        if [ "$waited" -ge "$PER_PORT_MAX_WAIT" ]; then
            echo " TIMEOUT after ${PER_PORT_MAX_WAIT}s"
            echo "ERROR: Endpoint on port $port did not start. Check vllm logs."
            exit 1
        fi
    done
    echo " OK (${waited}s)"
done
echo "[$(timestamp)] All 16 endpoints ready."

# Step 5: Run Evolution (5 iterations)
echo ""
echo "[$(timestamp)] Step 5/7: Running evolution pipeline..."
python scripts/run_evolution.py --config configs/default.yaml
echo "[$(timestamp)] Step 5 complete."

# Step 6: Run Benchmark
echo ""
echo "[$(timestamp)] Step 6/7: Running benchmark evaluation..."
python scripts/run_benchmark.py --config configs/default.yaml
echo "[$(timestamp)] Step 6 complete."

# Step 7: Print results
echo ""
echo "[$(timestamp)] Step 7/7: Results"
echo "=================================================="
echo "Evolution Log:"
python -c "
import json
log = json.load(open('results/evolution_log.json'))
for entry in log:
    i = entry['iteration']
    action = entry.get('action', '')
    val_acc = entry.get('val_acc', 0)
    train_acc = entry.get('train_acc', 0)
    n_skills = entry.get('n_skills', 0)
    n_tools = entry.get('n_tools', 0)
    print(f'  Iter {i}: train={train_acc:.4f}  val={val_acc:.4f}  action={action}  skills={n_skills}  tools={n_tools}')
"
echo ""
echo "Benchmark Results (Table 1):"
python -c "
import json
d = json.load(open('results/benchmark_results.json'))
for k in ['k2', 'k3', 'k4']:
    if k in d:
        acc = d[k].get('accuracy', 'N/A')
        n = d[k].get('n_total', 'N/A')
        print(f'  K={k[1]}: accuracy={acc:.4f}  (n={n})')
"
echo ""
echo "=================================================="
echo "Finished: $(timestamp)"
echo "=================================================="
