#!/usr/bin/env bash
# setup_env.sh — Environment setup for RewardHarness pipeline
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== RewardHarness Environment Setup ==="
echo "Project root: $PROJECT_ROOT"

# 1. Install dependencies
echo ""
echo "[1/3] Installing Python dependencies..."
if command -v uv &> /dev/null; then
    uv pip install -r "$PROJECT_ROOT/requirements.txt"
else
    echo "Warning: uv not found, falling back to pip"
    pip install -r "$PROJECT_ROOT/requirements.txt"
fi

# 2. Verify critical imports
echo ""
echo "[2/3] Verifying critical imports..."
python -c "import openai; print(f'  openai: {openai.__version__}')"
python -c "import datasets; print(f'  datasets: {datasets.__version__}')"
python -c "import yaml; print(f'  pyyaml: OK')"
python -c "import PIL; print(f'  pillow: OK')"
python -c "import numpy; print(f'  numpy: {numpy.__version__}')"

# 3. Check vLLM availability
echo ""
echo "[3/3] Checking vLLM..."
if python -c "import vllm; print(f'  vllm: {vllm.__version__}')" 2>/dev/null; then
    echo "  vLLM available (for serving)"
else
    echo "  vLLM not importable (OK if running on login node; needed on compute nodes)"
fi

# 4. Check Claude proxy availability
echo ""
echo "Checking Claude CLIProxyAPI at localhost:8317..."
if curl -sf http://127.0.0.1:8317/v1/models > /dev/null 2>&1; then
    echo "  Claude proxy: AVAILABLE"
else
    echo "  Claude proxy: NOT REACHABLE (ensure CLIProxyAPI is running before pipeline)"
fi

echo ""
echo "=== Setup complete ==="
