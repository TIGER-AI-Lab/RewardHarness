# RewardHarness

**Self-evolving agentic reward framework for image-editing evaluation.**

Code release for [*RewardHarness: Self-Evolving Agentic Post-Training*](https://arxiv.org/abs/2605.08703) (arXiv 2605.08703). Project page: [rewardharness.com](https://rewardharness.com).

RewardHarness reframes reward modeling as **context evolution** rather than weight optimization. From as few as ~100 preference demonstrations, an Orchestrator (Gemini) iteratively evolves a library of *Skills* (declarative scoring rubrics) and *Tools* (procedural in-context specs) that a frozen Sub-Agent (Qwen2.5-VL-7B via vLLM) consults at inference time. With 0.05% of the EditReward training data, RewardHarness reaches **47.4%** average accuracy on EditReward-Bench + GenAI-Bench, surpassing GPT-5 by 5.3 points.

## Architecture

```
Gemini orchestration layer            Qwen vLLM sub-agent + tools
  Router.prepare_context()              SubAgent.batch_evaluate()
  ChainAnalyzer.analyze()               Library.call_tool()
  Evolver._validate_tool()
```

| Module | What it does |
|---|---|
| `src/router.py` | Selects relevant Skills/Tools from the Library per editing prompt |
| `src/chain_analyzer.py` | Analyzes Sub-Agent reasoning chains → improvement signals (skill / tool updates) |
| `src/evolver.py` | Applies signals to the Library; validates new tool prompts via vLLM; snapshot/restore for rollback |
| `src/sub_agent.py` | Multi-turn Qwen reasoning with `<think>/<tool>/<obs>/<answer>` tags |
| `src/library/` | Skills (markdown rubrics) + Tools (VLM `system_prompt` specs) |
| `src/pipeline.py` | Evolution loop with Phase A (skills) / Phase B (tools) / Phase C (pruning) |

## Install

```bash
git clone https://github.com/TIGER-AI-Lab/RewardHarness.git
cd RewardHarness
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

```bash
# Vertex AI for the Gemini orchestrator
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/google-credentials.json"
export GEMINI_PROJECT="your-vertexai-project-id"
export GEMINI_LOCATION="global"
```

The Sub-Agent expects one or more vLLM endpoints serving `Qwen2.5-VL-7B-Instruct`. List them one URL per line in `configs/endpoints.txt`. Bring them up with `scripts/serve_vllm_multi.sh` (single node, multi-GPU) or `scripts/sbatch_vllm.sh` (Slurm).

## Quickstart

```bash
# Run all tests (~2 s, no GPU / no network needed)
python -m pytest tests/ -v

# Run evolution (main experiment) — Phase A/B/C loop on ~100 demos
python scripts/run_evolution.py \
  --config configs/default.yaml \
  --results-dir results/my_run/ \
  --max-iters 200

# Read-only benchmark (K=2/3/4 accuracy on EditReward-Bench)
python scripts/run_benchmark.py --config configs/default.yaml
```

## Reproduce paper results

End-to-end one-command reproduction (env setup → data download → vLLM serve → evolution → benchmark → print results):

```bash
bash scripts/reproduce.sh
```

The script needs **one machine with ≥ 4 GPUs (L40S / A100 / H100)**, the Gemini credentials above, and Internet access for the HuggingFace dataset download. It runs the 7 steps from `scripts/reproduce.sh` in order and trap-cleans up vLLM servers on exit. Total wall-clock: roughly 4–6 hours.

If you only want to **benchmark** an existing evolved library (skip evolution):

```bash
# Provide a checkpoint dir from a prior run
python scripts/run_benchmark.py \
  --config configs/default.yaml \
  --library-dir results/my_run/checkpoints/best
```

## Key config (`configs/default.yaml`)

```yaml
gemini:
  model: gemini-3.1-pro-preview     # orchestrator
evolution:
  train_n: 60                        # train split size
  val_n: 40                          # val split size
  augment_swap: true                 # A/B swap augmentation for position invariance
  explore_margin: 0.075              # keep if val_acc >= prev - margin
  prune_every_n: 50                  # periodic leave-one-out pruning
```

## Repository layout

```
RewardHarness/
├── src/                  # Orchestrator, Sub-Agent, Library, Pipeline
├── scripts/              # run_evolution.py, run_benchmark.py, vLLM launchers
├── tests/                # pytest suite (~100 tests)
├── configs/              # default.yaml + vLLM endpoints
├── vanilla/              # Baseline benchmark scripts (Claude, Gemini, etc.)
├── docs/                 # Design notes and plans
├── data/                 # Dataset checksums (run download_data.sh to populate)
└── score-guidelines/     # Reference rubrics
```

## Citation

```bibtex
@article{zhang2026rewardharness,
  title={RewardHarness: Self-Evolving Agentic Post-Training},
  author={Yuxuan Zhang and Penghui Du and Bo Li and Cong Wei and Junwen Miao and Huaisong Zhang and Songcheng Cai and Yubo Wang and Dongfu Jiang and Yuyu Zhang and Ping Nie and Wenhu Chen and Changqian Yu and Kelsey R. Allen},
  journal={arXiv preprint arXiv:2605.08703},
  year={2026}
}
```
