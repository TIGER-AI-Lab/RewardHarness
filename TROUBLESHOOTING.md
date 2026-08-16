# Troubleshooting

For v0.2 diagnostics, begin with `rewardharness check`. The historical
`python scripts/check_env.py` command delegates to the same implementation.

**Run the preflight first:**

```bash
make check    # or: python scripts/check_env.py
```

It will tell you exactly which of the items below is failing on your machine. If everything's green and you still hit an issue, the rest of this doc covers the long-tail fixes.

---

Common pitfalls and their fixes, ordered by where they tend to hit in a fresh setup. If your issue isn't listed, please open an [issue](https://github.com/TIGER-AI-Lab/RewardHarness/issues) with the failing command, the stack trace, and your Python / CUDA / `vllm` versions.

---

## Install

**`error: Failed to build vllm` / `ERROR: Could not build wheels for vllm`**
vLLM needs a matching CUDA toolchain. Either install pre-built wheels (`pip install vllm==<version>+cu121` per [vLLM docs](https://docs.vllm.ai/)) or skip vLLM entirely:

```bash
# Core deps only — enough for the test suite, examples/, and hosted-Sub-Agent benchmarks.
pip install -r requirements.txt
# Skip requirements-vllm.txt if you don't have a local GPU + matching CUDA.
```

**`ModuleNotFoundError: No module named 'src'`**
You're running scripts from the wrong directory. `cd` into the repo root before invoking `python scripts/...`, or install in editable mode:

```bash
pip install -e .
```

---

## Gemini / Vertex AI auth

**`google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials`**
The Orchestrator uses Vertex AI. Three env vars are required:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/your-service-account.json"
export GEMINI_PROJECT="your-vertexai-project-id"
export GEMINI_LOCATION="global"  # or us-central1 / europe-west4
```

Quick check:

```bash
python -c "from src.gemini_client import get_client; get_client(); print('OK')"
```

**`PermissionDenied: 403 Vertex AI API has not been used in project ... or it is disabled`**
Enable the Vertex AI API on the GCP project tied to your service-account key, and ensure the service account has `Vertex AI User` (`roles/aiplatform.user`).

**`NotFound: 404 Publisher Model ... was not found`**
The `gemini-3.1-pro-preview` model isn't yet GA in every region. Try `global` for `GEMINI_LOCATION`, or switch to a region with the preview enabled.

---

## vLLM endpoints

**`ConnectionError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded`**
No Sub-Agent is listening. Bring up an endpoint:

```bash
bash scripts/serve_vllm_multi.sh   # single-node, 4-GPU
# or
sbatch scripts/sbatch_vllm.sh      # Slurm
```

Then verify the endpoint is healthy before evolution:

```bash
curl -s http://localhost:8000/v1/models | jq .data[0].id
# → "Qwen2.5-VL-7B-Instruct"
```

(That's what `--served-model-name` resolves to in `scripts/serve_vllm_multi.sh`; the HuggingFace path `Qwen/Qwen2.5-VL-7B-Instruct` is the *weights*, not the served identifier.)

**`OutOfMemoryError: CUDA out of memory`**
Lower `GPU_MEM` (default 0.85, controls `--gpu-memory-utilization`) when launching `serve_vllm_multi.sh`, or shard the model across more GPUs with `--tensor-parallel-size`. Example:

```bash
GPU_MEM=0.6 bash scripts/serve_vllm_multi.sh
```

**Endpoints listed in `configs/endpoints.txt` but pipeline says "0 available"**
The Sub-Agent picks endpoints round-robin and removes any that fail a health check. Re-run the health probe in `scripts/reproduce.sh` step 4 to see which ports are responding.

**`openai.NotFoundError: Error code: 404 - model 'my-vlm' not found`** (or similar)
Mismatch between what the **client** asks for and what the vLLM **server** is serving. The Sub-Agent reads `REWARDHARNESS_SUBAGENT_MODEL` (default `Qwen2.5-VL-7B-Instruct`); the server's identifier is whatever `--served-model-name` was passed to `vllm.entrypoints.openai.api_server`. Both must match:

```bash
# Client side (what the pipeline asks for)
export REWARDHARNESS_SUBAGENT_MODEL="my-vlm"

# Server side — start vLLM with the same id
REWARDHARNESS_SUBAGENT_MODEL=my-vlm VLLM_MODEL_PATH=my-org/my-vlm \
    bash scripts/serve_vllm_multi.sh
```

Confirm by curling `/v1/models` and matching `data[0].id` against `$REWARDHARNESS_SUBAGENT_MODEL`. See README §"Swapping in a different VLM as Sub-Agent".

---

## Datasets

**`DatasetNotFoundError: Dataset 'TIGER-Lab/EditReward-Bench' doesn't exist`**
The benchmark dataset is gated. Accept the terms on the [HF page](https://huggingface.co/datasets/TIGER-Lab/EditReward-Bench) and `huggingface-cli login` before running.

**`huggingface_hub.errors.HfHubHTTPError: 401 Unauthorized`**
Set `HF_TOKEN` or run `huggingface-cli login` with a token that has read access.

---

## Evolution

**val_acc fluctuates between iterations — should I worry?**
No. Many proposed updates land and roll back. The Library is gated on `val_acc >= prev_val_acc - explore_margin` (default `0.075` in `configs/default.yaml`), so small dips are allowed on purpose to escape local minima. Catastrophic regressions roll back. The *best* checkpoint is the iteration with the highest `val_acc`, which `scripts/run_evolution.py` automatically surfaces at end-of-run:

```
Best iteration: 4 (val_acc=0.6000)  →  benchmark with
  --library-dir results/<run>/checkpoints/iter_4
```

Copy that command verbatim into `make benchmark` / `python scripts/run_benchmark.py` to evaluate the right checkpoint.

**10+ consecutive rollbacks during a run**
Usually means the Sub-Agent is producing unparseable outputs (vLLM endpoint flaking, or wrong prompt template). Check `results/<run>/evolution_log.json` for the last successful action and inspect the reasoning chain.

**Run dies mid-iteration**
The pipeline is checkpoint-resumable. Re-run the same `run_evolution.py` command with `--resume` — it'll pick up from the last completed iteration.

---

## Tests

**`pytest` collects but errors on import**
Almost always a missing core dependency. Re-install:

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

The full suite is mocked end-to-end (no GPU, no network, no real Gemini calls) and runs in ~2 s. If you see any test reach out over the network, file an issue — that's a regression.
