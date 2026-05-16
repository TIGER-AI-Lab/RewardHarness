# Output artifacts

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

A JSON array. One entry per iteration. Schema:

```jsonc
[
  {
    "iteration": 0,
    "train_acc": 0.4500,
    "val_acc": 0.4250,
    "best_val_acc": 0.4250,
    "action": "baseline",        // baseline | keep | rollback
    "skill_action": "skip",      // skip | keep | rollback (Phase A)
    "tool_action": "skip",       // skip | keep | rollback (Phase B)
    "val_acc_after_skills": null,
    "val_acc_after_tools": null,
    "n_skills": 0,
    "n_tools": 0
  },
  {
    "iteration": 1,
    "train_acc": 0.5167,
    "val_acc": 0.5000,           // val_acc after BOTH phases
    "prev_val_acc": 0.4250,      // running best at start of this iter
    "best_val_acc": 0.5000,
    "action": "keep",
    "skill_action": "keep",
    "tool_action": "rollback",   // Phase B rolled back; only Phase A stuck
    "val_acc_after_skills": 0.5000,
    "val_acc_after_tools": 0.4750,
    "n_skills": 1,
    "n_tools": 0
  }
  // …
]
```

**Reading it:** `action: "rollback"` means *both* skill and tool changes were undone (library restored to the pre-iteration snapshot). `action: "keep"` means at least one phase stuck. The official "best" checkpoint is the iteration whose `best_val_acc` is highest — pick it post-hoc, not the final iter.

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

```jsonc
{
  "k2": {
    "accuracy": 0.579,
    "n_total": 700,
    "n_correct": 405
  },
  "k3": {
    "accuracy": 0.467,
    "n_total": 350,
    "n_correct": 163
  },
  "k4": {
    "accuracy": 0.108,
    "n_total": 175,
    "n_correct": 19
  },
  "genai_bench": {
    "accuracy": 0.675,
    "n_total": 600
  }
}
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
