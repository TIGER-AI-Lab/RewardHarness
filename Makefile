.PHONY: help install check test demo evolve benchmark reproduce clean

# Default target: show available commands
help:
	@echo "RewardHarness — common targets"
	@echo ""
	@echo "  Target           What it does                                           Needs"
	@echo "  ---------------  ----------------------------------------------------  ---------------------"
	@echo "  make install     Install Python dependencies (core only)               nothing"
	@echo "  make test        Run the test suite                                    nothing (no GPU/net)"
	@echo "  make check       Preflight: verify env vars / creds / endpoints       nothing (probes only)"
	@echo "  make demo        1-iter smoke test from examples/seed_library          Gemini + vLLM (or HF)"
	@echo "  make benchmark   K=2/3/4 accuracy on EditReward-Bench (read-only)     Gemini + vLLM"
	@echo "  make evolve      Full evolution run (starts from empty library)        Gemini + vLLM"
	@echo "  make reproduce   End-to-end paper reproduction (~4-6 h)                Gemini + 4 GPUs"
	@echo "  make clean       Remove caches and generated artifacts                 nothing"
	@echo ""
	@echo "Gemini env vars (needed for everything except install / test / check / clean):"
	@echo "  GOOGLE_APPLICATION_CREDENTIALS  /path/to/service-account.json"
	@echo "  GEMINI_PROJECT                  your GCP project id"
	@echo "  GEMINI_LOCATION                 e.g. global (default)"
	@echo "See .env.example for the full list."

install:
	pip install -r requirements.txt

check:
	python scripts/check_env.py

test:
	python -m pytest tests/ -v

demo:
	python scripts/run_evolution.py \
	  --config configs/default.yaml \
	  --library-dir examples/seed_library \
	  --results-dir results/demo/ \
	  --max-iters 1

evolve:
	python scripts/run_evolution.py \
	  --config configs/default.yaml \
	  --results-dir results/my_run/ \
	  --max-iters 200

benchmark:
	python scripts/run_benchmark.py \
	  --config configs/default.yaml \
	  --library-dir examples/seed_library

reproduce:
	bash scripts/reproduce.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .coverage build dist *.egg-info
