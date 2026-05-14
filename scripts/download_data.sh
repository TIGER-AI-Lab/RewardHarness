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

# 3. Generate checksums
echo ""
echo "Generating checksums..."
CHECKSUM_FILE="$DATA_DIR/checksums.txt"
python -c "
import hashlib
import json
from datasets import load_dataset

results = {}

# Train data checksum
ds = load_dataset('AgPerry/EditReward-Data-100')
for split in ds:
    content = json.dumps([str(row) for row in ds[split]], sort_keys=True)
    h = hashlib.sha256(content.encode()).hexdigest()
    results[f'EditReward-Data-100/{split}'] = h
    print(f'  EditReward-Data-100/{split}: {h}')

# Benchmark checksum
ds = load_dataset('TIGER-Lab/EditReward-Bench')
for split in ds:
    content = json.dumps([str(row) for row in ds[split]], sort_keys=True)
    h = hashlib.sha256(content.encode()).hexdigest()
    results[f'EditReward-Bench/{split}'] = h
    print(f'  EditReward-Bench/{split}: {h}')

with open('$CHECKSUM_FILE', 'w') as f:
    for k, v in results.items():
        f.write(f'{v}  {k}\n')
print(f'  Checksums saved to $CHECKSUM_FILE')
"

echo ""
echo "=== Download complete ==="
