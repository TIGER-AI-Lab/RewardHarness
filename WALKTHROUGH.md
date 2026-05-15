# Walkthrough — from `git clone` to your first preference judgment

This walkthrough takes ~15 minutes if you only want to inspect the library and run the tests, and ~30 minutes (plus model-serving time) for a full `make demo` evolution pass. Each step is independent — feel free to stop after step 3 if you only want to understand the codebase.

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

By default this launches one vLLM endpoint per GPU on ports 8000+. Edit `configs/endpoints.txt` if you have a different layout. Verify with:

```bash
curl -s http://localhost:8000/v1/models | jq .data[0].id
# → "Qwen/Qwen2.5-VL-7B-Instruct"
```

## 7. One-iteration smoke test

```bash
make demo
```

Runs `scripts/run_evolution.py` for exactly one iteration over the 60-example training split and writes `results/demo/`. Walks through Router → Sub-Agent → ChainAnalyzer → Evolver once, so you can confirm the whole pipeline works on your hardware.

## 8. Full benchmark (read-only, requires an evolved Library)

If you have a prior `results/<run>/checkpoints/best/` from your own run:

```bash
python scripts/run_benchmark.py \
  --config configs/default.yaml \
  --library-dir results/<run>/checkpoints/best
```

Reports K=2/3/4 accuracy on EditReward-Bench and a single number on GenAI-Bench. With the paper's evolved Library this lands at **45.7%** average (Qwen Sub-Agent) or **47.4%** (Gemini-2.0-Flash Sub-Agent).

## 9. Full paper reproduction

```bash
make reproduce
```

End-to-end: env setup → dataset download → vLLM serve → 5-iteration evolution → benchmark → print results. Needs ≥4 GPUs and ~4–6 hours. See `scripts/reproduce.sh` for the step list.

---

## Where things live

| You want to … | Look at |
|---|---|
| Add a new Skill or Tool | `src/library/__init__.py` (`add_skill`, `add_tool`) |
| Change Sub-Agent prompts | `src/sub_agent.py` (`BASE_INSTRUCTIONS_NO_TOOLS`, `TOOL_INSTRUCTIONS`) |
| Tweak evolution gating | `src/pipeline.py` and `evolution.*` in `configs/default.yaml` |
| Add a new VLM backend | `src/sub_agent.py` (constructor accepts any OpenAI-compatible client) |
| Debug a single example | `examples/inspect_library.py` + `examples/show_reasoning_format.py` |

If something breaks, [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) covers the common failure modes.
