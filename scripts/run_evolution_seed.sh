#!/usr/bin/env bash
# Run evolution with a specific seed. Creates isolated library + results.
# Usage: bash scripts/run_evolution_seed.sh <seed> [max_iters]
set -uo pipefail

SEED="${1:?Usage: $0 <seed> [max_iters]}"
MAX_ITERS="${2:-10}"
PYTHON="${VLLM_PYTHON:-python}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Create seed-specific config
SEED_DIR="$PROJECT_ROOT/results/seed_${SEED}"
mkdir -p "$SEED_DIR"
LIB_DIR="$SEED_DIR/library"
mkdir -p "$LIB_DIR"
echo '{}' > "$LIB_DIR/registry.json"

# Create seed-specific config
cat > "$SEED_DIR/config.yaml" <<YAMLEOF
model:
  name: Qwen2.5-VL-7B-Instruct
  path: Qwen/Qwen2.5-VL-7B-Instruct
  max_model_len: 16384
  limit_mm_per_prompt_image: 5
  dtype: bfloat16
  gpu_memory_utilization: 0.85

claude:
  model: claude-sonnet-4-6

evolution:
  train_dataset: AgPerry/EditReward-Data-100
  train_n: 80
  val_n: 20
  max_iterations: ${MAX_ITERS}
  batch_concurrent: 128
  seed: ${SEED}

benchmark:
  dataset: TIGER-Lab/EditReward-Bench
  max_workers: 128
YAMLEOF

echo "=== Evolution seed=${SEED}, max_iters=${MAX_ITERS} ==="
echo "Library: $LIB_DIR"
echo "Config: $SEED_DIR/config.yaml"
echo "Start: $(date)"

$PYTHON "$PROJECT_ROOT/scripts/run_evolution.py" \
    --config "$SEED_DIR/config.yaml" \
    --library-dir "$LIB_DIR" \
    --max-iters "$MAX_ITERS" \
    2>&1

echo ""
echo "=== Evolution seed=${SEED} COMPLETE ==="
echo "End: $(date)"

# Copy evolution log to seed dir
cp "$PROJECT_ROOT/results/evolution_log.json" "$SEED_DIR/evolution_log.json" 2>/dev/null

# Run benchmark with this seed's library
echo ""
echo "=== Running benchmark for seed=${SEED} ==="
$PYTHON "$PROJECT_ROOT/scripts/run_benchmark.py" \
    --config "$SEED_DIR/config.yaml" \
    --library-dir "$LIB_DIR" \
    2>&1

cp "$PROJECT_ROOT/results/benchmark_results.json" "$SEED_DIR/benchmark_results.json" 2>/dev/null
echo "=== Benchmark seed=${SEED} COMPLETE ==="
