# Examples

Examples exercise the public `rewardharness.*` API and schema-v2 Library
format. Installed-package equivalents are listed by `rewardharness --help`.

Standalone scripts that you can run **without GPUs, vLLM, or API keys** to understand the RewardHarness internals before launching a full evolution.

| Item | What it shows |
|---|---|
| [`inspect_library.py`](inspect_library.py) | Five-minute tour of the Library data model: adding a Skill, adding a Tool, printing the registry, and round-tripping through disk. Requires `openai` + `pyyaml`. |
| [`show_reasoning_format.py`](show_reasoning_format.py) | Prints a representative `<think>/<tool>/<obs>/<answer>` chain so you know what to expect when running the real Sub-Agent. Pure stdlib. |
| [`score_pair.py`](score_pair.py) | End-to-end **real-models** demo: score a single edit pair through Library → Router → SubAgent. Needs Gemini + a vLLM endpoint (see .env.example). |
| [`seed_library/`](seed_library/) | Hand-curated starter Library (2 Skills + 1 Tool) so `scripts/run_benchmark.py --library-dir examples/seed_library` works immediately, without doing a 4–6 hour evolution first. |
| [`sample_evolution_log.json`](sample_evolution_log.json) | Illustrative 5-iteration evolution log so you can see the exact shape `results/<run>/evolution_log.json` will have (including `keep` / `rollback` actions and skill/tool counts). |
| [`sample_benchmark_results.json`](sample_benchmark_results.json) | Illustrative `benchmark_results.json` matching the paper's Qwen numbers on EditReward-Bench + GenAI-Bench. |

Run from the repo root:

```bash
python examples/inspect_library.py
python examples/show_reasoning_format.py
```

`inspect_library.py` prints a few "==>" sections (registry contents, skill markdown, round-trip assertion). `show_reasoning_format.py` prints one annotated preference judgment with the tag legend and the pipeline's parsing rules.

The `score_pair.py` real-models demo needs your own source + two candidate images plus an editing prompt:

```bash
python examples/score_pair.py \
    --source path/to/source.png \
    --candidate-a path/to/A.png \
    --candidate-b path/to/B.png \
    --prompt "Add a 'Sale' sign to the storefront" \
    --show-chain     # optional: also print the <think>/<tool>/<obs>/<answer> trace
```

It prints the resolved Sub-Agent model id and the endpoint count at startup, so a typo'd `REWARDHARNESS_SUBAGENT_MODEL` or empty `configs/endpoints.txt` is visible *before* the API call. To swap in a non-Qwen VLM, see [README §Swapping in a different VLM as Sub-Agent](../README.md#swapping-in-a-different-vlm-as-sub-agent).

## Using the seed library

```bash
# Benchmark with the hand-curated starter library (no evolution needed)
python scripts/run_benchmark.py \
  --config configs/default.yaml \
  --library-dir examples/seed_library

# Or use it as the *starting point* for your own evolution
python scripts/run_evolution.py \
  --config configs/default.yaml \
  --library-dir examples/seed_library \
  --results-dir results/from_seed/
```

The seed isn't the paper's evolved Library — it's a tiny illustrative starter so you don't have to begin from an empty registry. The paper's final 6-entry library (3 Skills + 3 Tools) is committed at [`rewardharness/resources/library/`](../rewardharness/resources/library/) and is what `make benchmark` benchmarks by default; `make reproduce` evolves a fresh library from scratch end-to-end.

If you want to see the Library in action against a real Sub-Agent, run `make demo` instead (1-iteration evolution; requires Gemini + a single vLLM endpoint).
