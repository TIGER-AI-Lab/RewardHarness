# Walkthrough — from `git clone` to your first preference judgment

The v0.2 examples prefer the unified `rewardharness` CLI. Historical script
entry points remain available as compatibility wrappers.

This walkthrough takes ~15 minutes if you only want to inspect the library and run the tests, and an additional ~3 minutes of pipeline work for a full `make demo` evolution pass — though vLLM cold-start can add 5&ndash;15 minutes the first time the model loads. Each step is independent — feel free to stop after step 3 if you only want to understand the codebase.

---

## 1. Clone and install (CPU-only, no Internet beyond pip)

```bash
git clone https://github.com/TIGER-AI-Lab/RewardHarness.git
cd RewardHarness
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

That's enough for steps 2–4. The optional `pip install -r requirements-vllm.txt` is **only** needed when you serve Qwen2.5-VL-7B locally (step 6).

## 2. Run the test suite (no GPU, no network)

```bash
make test
```

You should see `100 passed in ~2s`. Every external service (Gemini, vLLM, Hugging Face) is mocked, so if any test hits the network it's a regression — please [open an issue](https://github.com/TIGER-AI-Lab/RewardHarness/issues).

## 3. Inspect the data model

```bash
python examples/inspect_library.py
```

This adds one Skill (`realism-and-artifact-penalties`) and one Tool (`text-and-ocr-analyzer`) to a temp Library, prints the registry, and verifies a round-trip through disk. The Library is just markdown + YAML; understanding this file shape is the whole abstraction.

```bash
python examples/show_reasoning_format.py
```

Prints one full Sub-Agent trace (`<think>/<tool>/<obs>/<answer>` tags) so you know what the model outputs will look like.

## 4. Set up credentials

Copy the template and fill in real values:

```bash
cp .env.example .env
# edit .env in your editor
set -a; source .env; set +a   # exports every var into your shell
```

You'll need:
- A **Vertex AI service-account JSON** (`GOOGLE_APPLICATION_CREDENTIALS`)
- A **GCP project ID** with Vertex AI enabled (`GEMINI_PROJECT`)
- (Optional) a **Hugging Face token** (`HF_TOKEN`) for downloading the gated `TIGER-Lab/EditReward-Bench` dataset.

### Getting a Vertex AI service-account key (first time only)

If you don't already have one, here's the 5-minute path:

1. **Pick or create a GCP project** at <https://console.cloud.google.com/projectcreate>. Note the **Project ID** (not the friendly name) &mdash; e.g., `my-rh-project-12345`. Set `GEMINI_PROJECT` to this value.
2. **Enable the Vertex AI API**: <https://console.cloud.google.com/apis/library/aiplatform.googleapis.com> &rarr; pick your project &rarr; **Enable**.
3. **Create a service account**: <https://console.cloud.google.com/iam-admin/serviceaccounts> &rarr; **Create Service Account**. Give it any name (e.g., `rewardharness`). Grant it the **`Vertex AI User`** role (`roles/aiplatform.user`).
4. **Generate a JSON key**: click the service account &rarr; **Keys** &rarr; **Add Key** &rarr; **Create new key** &rarr; **JSON**. A `.json` file downloads. Move it somewhere safe &mdash; e.g., `~/.config/gcloud/rewardharness.json`.
5. **Point `GOOGLE_APPLICATION_CREDENTIALS` at that path** in your `.env`.

Confirm with `make check` (step 5 below) &mdash; it parses the JSON and reports the service-account email if things look right.

## 5. Preflight

```bash
make check    # or: python scripts/check_env.py
```

This catches every common misconfig (missing env var, malformed service-account JSON, unreachable endpoints) in ~10 seconds, instead of after a 4-hour evolution attempt.

## 6. Bring up a Sub-Agent (Qwen2.5-VL-7B via vLLM)

```bash
pip install -r requirements-vllm.txt
bash scripts/serve_vllm_multi.sh
```

By default this launches one vLLM endpoint per GPU on ports 8000+ (configurable via `NUM_GPUS`, `BASE_PORT`, `GPU_MEM`, …; see [`.env.example`](.env.example)). Edit `configs/endpoints.txt` if you have a different layout. Verify with:

```bash
curl -s http://localhost:8000/v1/models | jq .data[0].id
# → "Qwen2.5-VL-7B-Instruct"
```

(That's `--served-model-name` from `serve_vllm_multi.sh`, *not* the HuggingFace path `Qwen/Qwen2.5-VL-7B-Instruct`.) To swap in a different OpenAI-compatible VLM, set `REWARDHARNESS_SUBAGENT_MODEL` before serving and the rest of the pipeline picks it up &mdash; see README §"Swapping in a different VLM as Sub-Agent".

## 7. One-iteration smoke test

```bash
make demo
```

Runs `scripts/run_evolution.py` for exactly one iteration over the 60-example training split and writes `results/demo/`. Walks through Router → Sub-Agent → ChainAnalyzer → Evolver once, so you can confirm the whole pipeline works on your hardware.

## 8. Full benchmark (read-only)

You don't have to run evolution first &mdash; `rewardharness/resources/library/` ships with the paper's evolved Skills and Tools. To reproduce the paper's headline numbers against a hosted Sub-Agent, just point benchmark at the default (shipped) library:

```bash
python scripts/run_benchmark.py --config configs/default.yaml
```

That reports K=2/3/4 group accuracy on EditReward-Bench using the entries committed at `rewardharness/resources/library/`. The paper's **45.7%** average (Qwen Sub-Agent) and **47.4%** (Gemini-2.0-Flash Sub-Agent) headline numbers also include a separate GenAI-Bench pass; see [`OUTPUTS.md`](OUTPUTS.md#after-make-benchmark--scriptsrun_benchmarkpy) for the schema and the `jq` recipe to merge results from both passes.

To benchmark *your own* evolved Library from a prior run instead:

```bash
python scripts/run_benchmark.py \
  --config configs/default.yaml \
  --library-dir results/<run>/checkpoints/best
```

## 9. End-to-end EditReward-Bench reproduction

```bash
make reproduce
```

End-to-end: env setup → dataset download → vLLM serve → 5-iteration evolution → EditReward-Bench K=2/3/4 → print results. Needs ≥4 GPUs and ~4–6 hours. See `scripts/reproduce.sh` for the step list.

**If `make reproduce` dies partway through** (cluster preemption, vLLM crash, OOM): the evolution step is checkpoint-resumable. Skip the env+serve steps by hand and resume directly:

```bash
python scripts/run_evolution.py --config configs/default.yaml --resume
```

Then continue with `python scripts/run_benchmark.py --config configs/default.yaml`.

**To match the paper's full 47.4% / 45.7% headline**, also run a GenAI-Bench pass after `make reproduce` finishes and merge the two outputs &mdash; see [`OUTPUTS.md`](OUTPUTS.md#after-make-benchmark--scriptsrun_benchmarkpy) for the merge recipe. The paper headline is the mean of K=2, K=3, K=4, and GenAI-Bench accuracies.

---

## Where things live

| You want to … | Look at |
|---|---|
| Add a new Skill or Tool | `rewardharness/library/repository.py` (`add_skill`, `add_tool`) |
| Change Sub-Agent prompts | `rewardharness/evaluation/engine.py` (`BASE_INSTRUCTIONS_NO_TOOLS`, `TOOL_INSTRUCTIONS`) |
| Tweak evolution gating | `rewardharness/evolution/pipeline.py` and `evolution.*` in `configs/default.yaml` |
| Swap in a different OpenAI-compatible VLM | Export `REWARDHARNESS_SUBAGENT_MODEL=<your-model-id>`; point `configs/endpoints.txt` at your server. No source edit needed. |
| Add a non-OpenAI-compatible VLM backend | Subclass `SubAgent` in `rewardharness/evaluation/engine.py` and override `_call_vllm` (see README §Swapping Sub-Agent). |
| Debug a single example | `examples/inspect_library.py` + `examples/show_reasoning_format.py` |

If something breaks, [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) covers the common failure modes.
