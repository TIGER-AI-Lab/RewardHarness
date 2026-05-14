# RewardHarness

Self-evolving reward model for image editing quality evaluation.
Qwen2.5-VL-7B (vLLM) as Sub-Agent; Gemini `gemini-3.1-pro-preview` as orchestration layer (Router, ChainAnalyzer, Evolver).

## Architecture

```
Gemini (orch layer)          Qwen vLLM (sub-agent + tools)
  Router.prepare_context()     SubAgent.batch_evaluate()
  ChainAnalyzer.analyze()      Library.call_tool()
  Evolver._validate_tool()
```

- **Router** (`src/router.py`): selects relevant Skills/Tools from Library per editing prompt
- **ChainAnalyzer** (`src/chain_analyzer.py`): analyzes reasoning chains → improvement signals (skill_updates, tool_updates)
- **Evolver** (`src/evolver.py`): applies signals to Library; validates tool prompts via vLLM; snapshot/restore for rollback
- **SubAgent** (`src/sub_agent.py`): multi-turn Qwen reasoning with `<think>/<tool>/<obs>/<answer>` tags
- **Library** (`src/library/`): Skills (markdown evaluation guidance) + Tools (VLM system_prompts)
- **Pipeline** (`src/pipeline.py`): evolution loop with Phase A (skills) / Phase B (tools) / Phase C (pruning)

## Commands

```bash
# Tests (100 tests, ~2s)
python -m pytest tests/ -v

# Evolution (main experiment)
python scripts/run_evolution.py --config configs/default.yaml --results-dir results/<name>/ --max-iters 1000

# Benchmark (read-only, K=2/3/4 accuracy on EditReward-Bench)
python scripts/run_benchmark.py --config configs/default.yaml
```

## Key Config (`configs/default.yaml`)

```yaml
gemini:
  model: gemini-3.1-pro-preview    # orch layer model — do NOT use 2.5 models
evolution:
  train_n: 60                       # train split size
  val_n: 40                         # val split size
  augment_swap: true                # A/B swap augmentation for position invariance
  explore_margin: 0.075             # keep if val_acc >= prev - margin
  prune_every_n: 50                 # periodic leave-one-out pruning
```

## Environment

```bash
# Gemini auth (VertexAI) — see README for full setup
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/google-credentials.json"
export GEMINI_PROJECT="your-vertexai-project-id"
export GEMINI_LOCATION="global"
```

vLLM endpoints listed in `configs/endpoints.txt` (one URL per line). Start with `scripts/serve_vllm_multi.sh`.

## Rules

- **NO Claude API** in this project. Orch layer uses Gemini only. The old Claude proxy (`localhost:8317`) is dead.
- **NO Gemini 2.5 models**. Only `gemini-3.1-pro-preview` or newer.
- **SubAgent stays on Qwen vLLM** — never route sub-agent calls through Gemini.
- **Never import `anthropic`** or use `ANTHROPIC_API_KEY`.
- **Never reuse** code from `a-tool/edit-reward/` or `a-skill/` (buggy). Benchmark eval uses `TIGER-AI-Lab/EditReward` only.
- **Tests must pass** before any experiment run. Run `python -m pytest tests/ -v`.
- **Alert immediately** if 10+ consecutive rollbacks during evolution — don't wait.
- **Get user approval** before any git commit or push.
- **No `Co-Authored-By`** lines in commit messages.
