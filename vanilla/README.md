# Vanilla baselines

The ImagenHub TSVs include an additive `schema_version` column in v0.2. The
loaders exclude it from aggregation, and `scripts/check_rating_integrity.py`
proves that every original rating is preserved after projection.

Scripts that benchmark **off-the-shelf VLMs without any Skills/Tools library** — i.e., the raw model directly judging edits. Use these for the "Proprietary Models" and "Open-Source Models" rows of Table 1 in the paper.

## Layout

| Script | Routes through | Benchmark | Output |
|---|---|---|---|
| `bench_claude.py` | Dedicated Claude OpenAI-compatible proxy | EditReward-Bench | K=2/3/4 group accuracy |
| `bench_genaibench.py` | Dedicated Claude proxy | GenAI-Bench | pair-ranking accuracy |
| `bench_imagenhub.py` | Dedicated Claude proxy | ImagenHub (in-house raters) | Pearson correlation |
| `gemini_bench_claude.py` | Any OpenAI-compatible "Gemini gateway" | EditReward-Bench | K=2/3/4 group accuracy |
| `gemini_bench_genaibench.py` | Same Gemini gateway | GenAI-Bench | pair-ranking accuracy |
| `gemini_bench_imagenhub.py` | Same Gemini gateway | ImagenHub | Pearson correlation |

The `gemini_bench_*.py` group is named for the env-var family they consume (`GEMINI_GATEWAY_*`), not for being Gemini-only — the gateway is a multi-vendor OpenAI-compatible proxy, and `--model` can be a Gemini *or* Claude id (whatever your gateway accepts).

`imagenhub_data/rater{1,2,3}.tsv` are the three human-rater rows used to compute inter-annotator agreement on the ImagenHub split.

## Running

Each script takes a `--model` flag and an output JSON path.

| Script family | Auth env vars |
|---|---|
| `gemini_bench_*.py` (multi-vendor OpenAI-compatible gateway) | `GEMINI_GATEWAY_BASE_URL`, `GEMINI_GATEWAY_API_KEY` |
| `bench_*.py` (Claude OpenAI-compatible proxy) | `CLAUDE_API_BASE_URL`, `CLAUDE_API_KEY` |

If `CLAUDE_API_BASE_URL` / `CLAUDE_API_KEY` are unset, `bench_*.py` falls back to a localhost demo proxy that is unlikely to exist on your machine &mdash; set the two env vars to point at any OpenAI-compatible Claude endpoint (e.g. LiteLLM, an Anthropic-bridge gateway, or your own proxy).

Example:

```bash
python vanilla/gemini_bench_claude.py \
  --model gemini-2.0-flash \
  --output results/vanilla/gemini-2.0-flash_editrewardbench.json
```

These scripts intentionally don't share code with the `rewardharness` package — they're the "no library" reference point against which RewardHarness is measured.
