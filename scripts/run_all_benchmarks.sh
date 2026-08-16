#!/usr/bin/env bash
# Run benchmarks on ALL checkpoints (iter_0 through iter_9) sequentially.
# Each benchmark takes ~7 min, total ~70 min.
# Results saved to results/benchmark_iter_N.json
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

PYTHON="${VLLM_PYTHON:-python}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$PROJECT_ROOT/configs/default.yaml"
CHECKPOINTS_DIR="$PROJECT_ROOT/results/checkpoints"
RESULTS_DIR="$PROJECT_ROOT/results"

echo "=== Running ALL benchmarks ==="
echo "Start: $(date)"

for iter_dir in "$CHECKPOINTS_DIR"/iter_*; do
    iter_num=$(basename "$iter_dir" | sed 's/iter_//')
    outfile="$RESULTS_DIR/benchmark_iter_${iter_num}.json"

    echo ""
    echo "============================================================"
    echo "Benchmark: iter_${iter_num} ($(date))"
    echo "Library dir: $iter_dir"
    echo "Output: $outfile"
    echo "============================================================"

    # Point benchmark at this checkpoint's library
    $PYTHON "$PROJECT_ROOT/scripts/run_benchmark.py" \
        --config "$CONFIG" \
        --library-dir "$iter_dir" \
        2>&1

    # Move the result file
    if [ -f "$RESULTS_DIR/benchmark_results.json" ]; then
        cp "$RESULTS_DIR/benchmark_results.json" "$outfile"
        echo "Saved: $outfile"
    fi
done

echo ""
echo "=== ALL BENCHMARKS COMPLETE ==="
echo "End: $(date)"
echo ""

# Summary table. K=2/3/4 are always present (run_benchmark.py writes them);
# GenAI and Avg appear only if a separate GenAI-Bench pass was merged in
# (see OUTPUTS.md). Missing keys render as '—' rather than 0.0000 so the
# table doesn't lie about scores it doesn't actually have.
echo "Iter | K=2    | K=3    | K=4    | GenAI  | Avg"
echo "-----|--------|--------|--------|--------|--------"
for iter_dir in "$CHECKPOINTS_DIR"/iter_*; do
    iter_num=$(basename "$iter_dir" | sed 's/iter_//')
    outfile="$RESULTS_DIR/benchmark_iter_${iter_num}.json"
    if [ -f "$outfile" ]; then
        $PYTHON -c "
import json, sys
d = json.load(open(sys.argv[1]))
def fmt(key, top=False):
    v = d.get(key) if top else (d.get(key, {}) or {}).get('accuracy')
    if v is None:
        return '   —   '
    return f'{v:.4f}'
def acc(key):
    sub = d.get(key)
    if isinstance(sub, dict) and 'accuracy' in sub:
        return f\"{sub['accuracy']:.4f}\"
    return '   —   '
print(f'  {sys.argv[2]}  | {acc(\"k2\")} | {acc(\"k3\")} | {acc(\"k4\")} | {acc(\"genai_bench\")} | {fmt(\"average\", top=True)}')
" "$outfile" "$iter_num"
    fi
done
