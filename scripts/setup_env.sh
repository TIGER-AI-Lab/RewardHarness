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

# 4. Check Gemini / Vertex AI environment
echo ""
echo "[4/5] Checking Gemini / Vertex AI env..."
for var in GOOGLE_APPLICATION_CREDENTIALS GEMINI_PROJECT; do
    if [ -z "${!var:-}" ]; then
        echo "  $var: NOT SET (required — see .env.example)"
    else
        echo "  $var: set"
    fi
done

# 5. Check at least one vLLM endpoint from configs/endpoints.txt
echo ""
echo "[5/5] Checking vLLM endpoints..."
EP_FILE="$PROJECT_ROOT/configs/endpoints.txt"
if [ -f "$EP_FILE" ]; then
    ANY_OK=0
    while IFS= read -r url; do
        [[ -z "$url" || "$url" =~ ^# ]] && continue
        if curl -sf --max-time 3 "$url/models" > /dev/null 2>&1; then
            echo "  $url: REACHABLE"
            ANY_OK=1
        else
            echo "  $url: not reachable"
        fi
    done < "$EP_FILE"
    if [ "$ANY_OK" = "0" ]; then
        echo "  (no endpoint reachable yet — bring one up with scripts/serve_vllm_multi.sh)"
    fi
else
    echo "  $EP_FILE not found"
fi

echo ""
echo "=== Setup complete ==="
