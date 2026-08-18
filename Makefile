.PHONY: help install install-dev check test quality release-check demo evolve benchmark reproduce clean

# Default target: show available commands
help:
	@echo "RewardHarness — common targets"
	@echo ""
	@echo "  Target           What it does                                           Needs"
	@echo "  ---------------  ----------------------------------------------------  ---------------------"
	@echo "  make install     Install Python dependencies (core only)               nothing"
	@echo "  make install-dev Install test and release tooling                      nothing"
	@echo "  make test        Run the test suite                                    nothing (no GPU/net)"
	@echo "  make quality     Run lint, types, data integrity, and shell checks     dev dependencies"
	@echo "  make release-check  Build and validate wheel + source distribution     nothing"
	@echo "  make check       Preflight: verify env vars / creds / endpoints       nothing (probes only)"
	@echo "  make demo        1-iter smoke test from examples/seed_library          Gemini + vLLM (or HF)"
	@echo "  make benchmark   K=2/3/4 accuracy on EditReward-Bench (read-only)     Gemini + vLLM"
	@echo "  make evolve      Evolve packaged library for 200 iters → results/my_run/ Gemini + vLLM"
	@echo "  make reproduce   End-to-end EditReward-Bench reproduction (~4-6 h)    Gemini + 4 GPUs"
	@echo "  make clean       Remove caches and generated artifacts                 nothing"
	@echo ""
	@echo "Gemini env vars (needed for everything except install / test / check / clean):"
	@echo "  GOOGLE_APPLICATION_CREDENTIALS  /path/to/service-account.json"
	@echo "  GEMINI_PROJECT                  your GCP project id"
	@echo "  GEMINI_LOCATION                 e.g. global (default)"
	@echo "See .env.example for the full list."

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

check:
	python scripts/check_env.py

test:
	python -m pytest tests/ -v --cov=rewardharness --cov-report=term-missing

quality:
	ruff format --check rewardharness src scripts examples tests vanilla
	ruff check rewardharness src scripts examples tests vanilla
	mypy rewardharness scripts/check_distribution.py scripts/check_release_metadata.py
	python scripts/check_rating_integrity.py
	python scripts/check_migration_coverage.py
	python scripts/check_release_metadata.py
	pip-audit -r requirements.txt
	@for file in scripts/*.sh scripts/lib/*.sh; do bash -n "$$file"; done
	@if command -v shellcheck >/dev/null 2>&1; then shellcheck scripts/*.sh scripts/lib/*.sh; \
	else echo "shellcheck not installed; bash syntax checks completed"; fi

release-check: quality test
	rm -rf build dist rewardharness.egg-info
	python -m build
	python -m twine check dist/*
	python scripts/check_distribution.py

demo:
	rewardharness evolve \
	  --config configs/default.yaml \
	  --library-dir examples/seed_library \
	  --results-dir results/demo/ \
	  --max-iters 1

evolve:
	rewardharness evolve \
	  --config configs/default.yaml \
	  --results-dir results/my_run/ \
	  --max-iters 200

benchmark:
	rewardharness benchmark \
	  --config configs/default.yaml
# Defaults to the paper-evolved library shipped as package resources and reports
# K=2/3/4 accuracy on EditReward-Bench. The paper's headline 45.7% / 47.4%
# average is mean(K=2, K=3, K=4, GenAI-Bench) — for the GenAI-Bench column
# you need a separate eval pass (see OUTPUTS.md §"After make benchmark").
# To benchmark a different library — e.g. one you evolved yourself or the
# small examples/seed_library/ — call the CLI with
# --library-dir <path>.

reproduce:
	bash scripts/reproduce.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .coverage build dist *.egg-info
