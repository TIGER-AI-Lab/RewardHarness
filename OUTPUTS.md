# Output artifacts

v0.2 checkpoints and Library registries carry `schema_version: 2`. Readers
accept v0.1 registries and checkpoints, while all new writes use versioned
metadata.

What gets written where after each RewardHarness command, so you know what to expect, what to keep, and what to ignore. Paths shown here are the defaults; everything is overridable via `--results-dir` on the CLI.

---

## After `make demo` / `make evolve` / `scripts/run_evolution.py`

```
results/<run>/
├── evolution_log.json        # one entry per iteration
├── checkpoints/
│   ├── iter_0/               # baseline snapshot (empty library)
│   │   ├── registry.json
│   │   └── metadata.json
│   ├── iter_1/
│   │   ├── registry.json
│   │   ├── skills/<name>/SKILL.md
│   │   ├── tools/<name>/SKILL.md
│   │   └── metadata.json
│   └── …
└── evolution_run.log         # stdout/stderr if launched via reproduce.sh
```

### `evolution_log.json`

See [`examples/sample_evolution_log.json`](examples/sample_evolution_log.json) for a full 5-iteration sample you can `jq`/diff against your own runs.

A JSON array. One entry per iteration. Schema:

```jsonc
[
  {
    "iteration": 0,
    "train_acc": 0.4500,
    "val_acc": 0.4250,
    "best_val_acc": 0.4250,
    "action": "baseline",          // baseline | keep | rollback
    "skill_action": "skip",        // skip | keep | rollback (Phase A)
    "tool_action": "skip",         // skip | keep | rollback (Phase B)
    "val_acc_after_skills": null,
    "val_acc_after_tools": null,
    "n_skills": 0,
    "n_tools": 0,
    "duration_s": 30.2             // wall-clock per iter, in seconds
  },
  {
    "iteration": 1,
    "train_acc": 0.5167,
    "val_acc": 0.5000,             // val_acc after BOTH phases
    "prev_val_acc": 0.4250,        // running best at start of this iter
    "best_val_acc": 0.5000,
    "action": "keep",
    "skill_action": "keep",
    "tool_action": "rollback",     // Phase B rolled back; only Phase A stuck
    "val_acc_after_skills": 0.5000,
    "val_acc_after_tools": 0.4750,
    "applied": {                   // counts of changes the Evolver applied this iter
      "skills_added": 1, "skills_updated": 0, "skills_deleted": 0,
      "tools_added": 0, "tools_updated": 1, "tools_deleted": 0
    },
    "analysis_summary": "Sub-Agent missed OCR failures in 3/12 examples; …",
    "pruned": [],                  // entries removed by Phase-C periodic pruning (mostly empty)
    "n_skills": 1,
    "n_tools": 0,
    "duration_s": 124.5
  }
  // …
]
```

**Reading it:** `action: "rollback"` means *both* skill and tool changes were undone (library restored to the pre-iteration snapshot). `action: "keep"` means at least one phase stuck. The official "best" checkpoint is the iteration whose `val_acc` is highest — pick it post-hoc, not the final iter. `scripts/run_evolution.py` prints this for you at the end of every run:

```
Best iteration: 4 (val_acc=0.6000)  →  benchmark with
  --library-dir results/<run>/checkpoints/iter_4
```

### `checkpoints/iter_N/`

| File | Contents |
|---|---|
| `registry.json` | Library registry at end of iteration N (name → `{type, description, path}`). |
| `skills/<name>/SKILL.md` | Each Skill's markdown body with YAML frontmatter. |
| `tools/<name>/SKILL.md` | Each Tool's markdown body with YAML frontmatter (incl. `system_prompt`, `input_schema`, `output_schema`). |
| `metadata.json` | `{iteration, val_acc, best_val_acc, snap}` — what `_load_checkpoint` consumes on resume. |

To benchmark a specific checkpoint without re-evolving:

```bash
python scripts/run_benchmark.py \
  --config configs/default.yaml \
  --library-dir results/<run>/checkpoints/iter_N
```

---

## After `make benchmark` / `scripts/run_benchmark.py`

```
results/
└── benchmark_results.json
```

### `benchmark_results.json`

`scripts/run_benchmark.py` writes the **EditReward-Bench K=2/3/4** block — three keys, one per group size:

```jsonc
{
  "k2": { "accuracy": 0.579, "n_total": 700, "n_correct": 405, "n_pairs": 700, "pair_results": [...] },
  "k3": { "accuracy": 0.467, "n_total": 350, "n_correct": 163, "n_pairs": 1050, "pair_results": [...] },
  "k4": { "accuracy": 0.108, "n_total": 175, "n_correct":  19, "n_pairs": 1050, "pair_results": [...] }
}
```

The illustrative sample at [`examples/sample_benchmark_results.json`](examples/sample_benchmark_results.json) also carries paper-reference fields that `run_benchmark.py` itself does NOT compute — they reflect the paper's full evaluation, which includes an additional GenAI-Bench pass on top of EditReward-Bench:

```jsonc
{
  // ---- Run metadata you may add yourself for cross-run comparison ----
  "_about":        "Illustrative — paper's full pipeline output, not direct run_benchmark.py output",
  "_library_dir":  "results/my_run/checkpoints/best",
  "_orchestrator": "gemini-3.1-pro-preview",
  "_sub_agent":    "Qwen2.5-VL-7B-Instruct (via vLLM)",
  // ---- Paper headline (requires combining run_benchmark.py output with a separate
  //      GenAI-Bench pass — see vanilla/*_genaibench.py for the baseline scripts) ----
  "average":       0.457,                              // mean of the four sub-scores below
  "genai_bench":   { "accuracy": 0.675, "n_total": 600, "n_correct": 405 }
}
```

Keys prefixed with `_` are run-context metadata you can drop in by hand or via a wrapper script (e.g. `scripts/run_all_benchmarks.sh`); `genai_bench` and `average` need a separate GenAI-Bench evaluation pass and are not written by `run_benchmark.py` directly. Use `jq` to merge:
```bash
jq -s '.[0] * .[1]' editreward_results.json genai_bench_results.json > combined.json
```

Compare against the headline numbers in [`CHANGELOG.md`](CHANGELOG.md) for the v0.1.0 release: Qwen Sub-Agent reaches K=2: 57.9 / K=3: 46.7 / K=4: 10.8 / GenAI-Bench: 67.5; Gemini-2.0-Flash Sub-Agent reaches K=2: 66.2 / K=3: 45.3 / K=4: 13.5 / GenAI-Bench: 64.4.

---

## After `make reproduce` / `scripts/reproduce.sh`

Everything above, plus printed-to-stdout summaries of `evolution_log.json` and `benchmark_results.json` for quick comparison against the paper table. The vLLM endpoints are auto-cleaned on exit via the trap in `reproduce.sh`.

---

## Disk usage

Per evolution run, expect:

| What | Size |
|---|---|
| `evolution_log.json` | a few KB |
| `checkpoints/` (5 iterations) | 30–80 KB (markdown files dominate) |
| Cached datasets in `~/.cache/huggingface/datasets/` | ~2 GB (EditReward-Bench + EditReward-Data-100) |

vLLM model weights (`~/.cache/huggingface/hub/`) are ~15 GB for Qwen2.5-VL-7B-Instruct — not counted here because they're shared across runs.
