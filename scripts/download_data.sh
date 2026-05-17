#!/usr/bin/env bash
# download_data.sh — Download datasets for RewardHarness pipeline
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"

mkdir -p "$DATA_DIR"

echo "=== Downloading RewardHarness datasets ==="

# 1. Download training data
echo ""
echo "[1/2] Downloading AgPerry/EditReward-Data-100 (evolution train/val)..."
python -c "
from datasets import load_dataset
ds = load_dataset('AgPerry/EditReward-Data-100')
print(f'  Loaded: {ds}')
for split in ds:
    print(f'  {split}: {len(ds[split])} examples')
    print(f'  Columns: {ds[split].column_names}')
print('  First example keys:', list(ds[list(ds.keys())[0]][0].keys()))
"

# 2. Download benchmark data
echo ""
echo "[2/2] Downloading TIGER-Lab/EditReward-Bench (benchmark eval)..."
python -c "
from datasets import load_dataset
ds = load_dataset('TIGER-Lab/EditReward-Bench')
print(f'  Loaded: {ds}')
for split in ds:
    print(f'  {split}: {len(ds[split])} examples')
"

echo ""
echo "=== Download complete ==="
echo "Both datasets are cached in ~/.cache/huggingface/. To verify your copy"
echo "matches the paper's, compare each split's HF fingerprint:"
echo "  python -c \"from datasets import load_dataset; \\"
echo "             print(load_dataset('TIGER-Lab/EditReward-Bench')['train']._fingerprint)\""
