# RewardHarness

[![arXiv](https://img.shields.io/badge/arXiv-2605.08703-b31b1b.svg)](https://arxiv.org/abs/2605.08703)
[![Project Page](https://img.shields.io/badge/Project-rewardharness.com-6D7CFF.svg)](https://rewardharness.com)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Self-evolving agentic reward framework for image-editing evaluation.**

Code release for [*RewardHarness: Self-Evolving Agentic Post-Training*](https://arxiv.org/abs/2605.08703) (arXiv 2605.08703). Project page: [rewardharness.com](https://rewardharness.com).

## Updates

- **2026-05-14** — Initial open-source release at [`TIGER-AI-Lab/RewardHarness`](https://github.com/TIGER-AI-Lab/RewardHarness).
- **2026-05-09** — Paper on arXiv: [2605.08703](https://arxiv.org/abs/2605.08703).

RewardHarness reframes reward modeling as **context evolution** rather than weight optimization. From as few as ~100 preference demonstrations, an Orchestrator (Gemini) iteratively evolves a library of *Skills* (declarative scoring rubrics) and *Tools* (procedural in-context specs) that a frozen Sub-Agent (Qwen2.5-VL-7B via vLLM) consults at inference time. With 0.05% of the EditReward training data, RewardHarness reaches **47.4%** average accuracy on EditReward-Bench + GenAI-Bench, surpassing GPT-5 by 5.3 points.

## Architecture

```mermaid
flowchart LR
    subgraph IN["Input"]
      Is["Source image"]
      P["Editing prompt"]
      Ik["K candidate edits"]
    end

    subgraph ORC["Orchestrator (Gemini)"]
      R["Router"]
      CA["Chain Analyzer"]
      EV["Evolver"]
    end

    subgraph LIB["Library (versioned)"]
      SK["Skills (rubrics)"]
      TL["Tools (system_prompts)"]
    end

    subgraph SUB["Sub-Agent (frozen Qwen2.5-VL-7B via vLLM)"]
      RC["Reasoning chain"]
      OUT["Scores + ranking"]
    end

    IN --> R
    LIB -- "selected subset" --> R
    R -- "context C" --> SUB
    SUB --> OUT
    OUT -- "vs. ground truth" --> CA
    CA -- "improvement signals" --> EV
    EV -- "skill / tool updates (gated)" --> LIB
```

At **inference**, the Router selects relevant entries from the Library and the frozen Sub-Agent builds a reasoning chain that produces a preference judgment. At **evolution**, the Chain Analyzer compares predictions against ~100 ground-truth labels and the Evolver applies skill/tool updates — keeping each update only if held-out validation accuracy improves.

| Module | What it does |
|---|---|
| `src/router.py` | Selects relevant Skills/Tools from the Library per editing prompt |
| `src/chain_analyzer.py` | Analyzes Sub-Agent reasoning chains → improvement signals (skill / tool updates) |
| `src/evolver.py` | Applies signals to the Library; validates new tool prompts via vLLM; snapshot/restore for rollback |
| `src/sub_agent.py` | Multi-turn Qwen reasoning with `<think>/<tool>/<obs>/<answer>` tags |
| `src/library/` | Skills (markdown rubrics) + Tools (VLM `system_prompt` specs) |
| `src/pipeline.py` | Evolution loop with Phase A (skills) / Phase B (tools) / Phase C (pruning) |

## Hardware requirements

| Workflow | Minimum |
|---|---|
| Test suite, `examples/inspect_library.py`, library inspection | CPU only, no Internet |
| Benchmark with a hosted Sub-Agent (Gemini drop-in) | CPU only + Gemini API |
| Local Qwen2.5-VL-7B Sub-Agent for evolution / full benchmark | **1 × GPU with ≥ 24 GB** (L40S / A100 / H100); 4 GPUs recommended for parallel evaluation |
| Full paper reproduction (`make reproduce`) | **≥ 4 GPUs**, ~4–6 h wall-clock, ~50 GB free disk |

## Install

```bash
git clone https://github.com/TIGER-AI-Lab/RewardHarness.git
cd RewardHarness
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# OPTIONAL — only needed if you'll serve Qwen2.5-VL-7B locally with vLLM.
# Skip this if you only want to run the test suite, inspect the Library, or
# point the Sub-Agent at a hosted Gemini endpoint instead.
pip install -r requirements-vllm.txt
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
# Preflight: verify env vars, credentials, and endpoint reachability
make check         # or: python scripts/check_env.py

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
model:                                 # Sub-Agent (vLLM)
  name: Qwen2.5-VL-7B-Instruct
  path: Qwen/Qwen2.5-VL-7B-Instruct    # HF repo id or local path
  max_model_len: 16384                 # context window
  limit_mm_per_prompt_image: 5         # max images per call
  dtype: bfloat16
  gpu_memory_utilization: 0.85         # lower if you hit OOM

gemini:                                # Orchestrator
  model: gemini-3.1-pro-preview        # 3.1 only — do NOT downgrade to 2.5

evolution:
  train_dataset: AgPerry/EditReward-Data-100   # 100 preference demos
  train_n: 60                          # train split size
  val_n: 40                            # val split size (gating)
  max_iterations: 5                    # iterations per run
  batch_concurrent: 128                # parallel Sub-Agent calls
  explore_margin: 0.075                # keep if val_acc >= prev - margin
  augment_swap: true                   # A/B swap augmentation
  prune_every_n: 50                    # periodic leave-one-out pruning
  seed: 42

benchmark:
  dataset: TIGER-Lab/EditReward-Bench
  max_workers: 128                     # parallel scoring threads
```

## Repository layout

```
RewardHarness/
├── src/                  # Orchestrator, Sub-Agent, Library, Pipeline
├── scripts/              # run_evolution.py, run_benchmark.py, vLLM launchers
├── tests/                # pytest suite (~100 tests)
├── configs/              # default.yaml + vLLM endpoints
├── vanilla/              # Baseline benchmark scripts (Claude, Gemini, etc.)
├── score-guidelines/     # Reference rubrics
├── data/                 # Dataset checksums (run download_data.sh to populate)
├── Makefile              # `make help` lists install / test / demo / benchmark / reproduce
├── CITATION.cff          # GitHub-rendered "Cite this repository" widget
├── LICENSE               # Apache 2.0
└── requirements.txt      # Python dependencies
```

## Troubleshooting

Hit a wall? See [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) for fixes to common install / auth / vLLM / dataset pitfalls.

## Citation

```bibtex
@article{zhang2026rewardharness,
  title={RewardHarness: Self-Evolving Agentic Post-Training},
  author={Yuxuan Zhang and Penghui Du and Bo Li and Cong Wei and Junwen Miao and Huaisong Zhang and Songcheng Cai and Yubo Wang and Dongfu Jiang and Yuyu Zhang and Ping Nie and Wenhu Chen and Changqian Yu and Kelsey R. Allen},
  journal={arXiv preprint arXiv:2605.08703},
  year={2026}
}
```
