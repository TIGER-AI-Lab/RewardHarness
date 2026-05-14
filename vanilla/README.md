# Vanilla baselines

Scripts that benchmark **off-the-shelf VLMs without any Skills/Tools library** — i.e., the raw model directly judging edits. Use these for the "Proprietary Models" and "Open-Source Models" rows of Table 1 in the paper.

## Layout

| Script | Backend | Benchmark | Output |
|---|---|---|---|
| `bench_claude.py` | Anthropic Claude (OpenAI-compatible proxy) | EditReward-Bench | K=2/3/4 group accuracy |
| `bench_genaibench.py` | Anthropic Claude (proxy) | GenAI-Bench | pair-ranking accuracy |
| `bench_imagenhub.py` | Anthropic Claude (proxy) | ImagenHub (in-house raters) | Pearson correlation |
| `bench_wanqing.py` | (research-private benchmark) | held-out set | per-criterion |
| `gemini_bench_claude.py` | Google Gemini (Vertex AI) | EditReward-Bench | K=2/3/4 group accuracy |
| `gemini_bench_genaibench.py` | Google Gemini | GenAI-Bench | pair-ranking accuracy |
| `gemini_bench_imagenhub.py` | Google Gemini | ImagenHub | Pearson correlation |

`imagenhub_data/rater{1,2,3}.tsv` are the three human-rater rows used to compute inter-annotator agreement on the ImagenHub split.

## Running

Each script takes a `--model` flag and an output JSON path. They expect the same `GOOGLE_APPLICATION_CREDENTIALS` / `GEMINI_PROJECT` env vars as the main pipeline (Gemini scripts), or a Claude-compatible base URL (`bench_claude.py`).

Example:

```bash
python vanilla/gemini_bench_claude.py \
  --model gemini-2.0-flash \
  --output results/vanilla/gemini-2.0-flash_editrewardbench.json
```

These scripts intentionally don't share code with `src/` — they're the "no library" reference point against which RewardHarness is measured.
