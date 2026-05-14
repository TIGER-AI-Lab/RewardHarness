.PHONY: help install test demo evolve benchmark reproduce clean

# Default target: show available commands
help:
	@echo "RewardHarness — common targets"
	@echo ""
	@echo "  make install     Install Python dependencies"
	@echo "  make test        Run the test suite (no GPU / no network)"
	@echo "  make demo        Run a 1-iteration evolution smoke test"
	@echo "  make evolve      Full evolution run (configs/default.yaml)"
	@echo "  make benchmark   K=2/3/4 accuracy on EditReward-Bench (read-only)"
	@echo "  make reproduce   End-to-end paper reproduction (≥ 4 GPUs, ~4-6 h)"
	@echo "  make clean       Remove caches and generated artifacts"
	@echo ""
	@echo "Required env vars (Gemini orchestrator):"
	@echo "  GOOGLE_APPLICATION_CREDENTIALS, GEMINI_PROJECT, GEMINI_LOCATION"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

demo:
	python scripts/run_evolution.py \
	  --config configs/default.yaml \
	  --results-dir results/demo/ \
	  --max-iters 1

evolve:
	python scripts/run_evolution.py \
	  --config configs/default.yaml \
	  --results-dir results/my_run/ \
	  --max-iters 200

benchmark:
	python scripts/run_benchmark.py --config configs/default.yaml

reproduce:
	bash scripts/reproduce.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .coverage build dist *.egg-info
