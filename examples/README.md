# Examples

Standalone scripts that you can run **without GPUs, vLLM, or API keys** to understand the RewardHarness internals before launching a full evolution.

| Item | What it shows |
|---|---|
| [`inspect_library.py`](inspect_library.py) | Five-minute tour of the Library data model: adding a Skill, adding a Tool, printing the registry, and round-tripping through disk. Requires `openai` + `pyyaml`. |
| [`show_reasoning_format.py`](show_reasoning_format.py) | Prints a representative `<think>/<tool>/<obs>/<answer>` chain so you know what to expect when running the real Sub-Agent. Pure stdlib. |
| [`seed_library/`](seed_library/) | Hand-curated starter Library (2 Skills + 1 Tool) so `scripts/run_benchmark.py --library-dir examples/seed_library` works immediately, without doing a 4–6 hour evolution first. |

Run from the repo root:

```bash
python examples/inspect_library.py
python examples/show_reasoning_format.py
```

`inspect_library.py` prints a few "==>" sections (registry contents, skill markdown, round-trip assertion). `show_reasoning_format.py` prints one annotated preference judgment with the tag legend and the pipeline's parsing rules.

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

The seed isn't the paper's evolved Library — it's a tiny illustrative starter so you don't have to begin from an empty registry. The paper's full 7-entry final library is reproduced via `make reproduce`.

If you want to see the Library in action against a real Sub-Agent, run `make demo` instead (1-iteration evolution; requires Gemini + a single vLLM endpoint).
