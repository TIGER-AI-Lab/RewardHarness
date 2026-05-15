# Troubleshooting

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
# → "Qwen/Qwen2.5-VL-7B-Instruct"
```

**`OutOfMemoryError: CUDA out of memory`**
Lower `--gpu-memory-utilization` (default 0.9) in `serve_vllm_multi.sh`, or shard the model across more GPUs with `--tensor-parallel-size`.

**Endpoints listed in `configs/endpoints.txt` but pipeline says "0 available"**
The Sub-Agent picks endpoints round-robin and removes any that fail a health check. Re-run the health probe in `scripts/reproduce.sh` step 4 to see which ports are responding.

---

## Datasets

**`DatasetNotFoundError: Dataset 'TIGER-Lab/EditReward-Bench' doesn't exist`**
The benchmark dataset is gated. Accept the terms on the [HF page](https://huggingface.co/datasets/TIGER-Lab/EditReward-Bench) and `huggingface-cli login` before running.

**`huggingface_hub.errors.HfHubHTTPError: 401 Unauthorized`**
Set `HF_TOKEN` or run `huggingface-cli login` with a token that has read access.

---

## Evolution

**`AssertionError: validation accuracy not strictly monotonic`**
Expected — many proposed updates roll back. The Library is gated on `>= prev - explore_margin` (default `0.075`), and the *best* checkpoint is selected post-hoc from `results/<run>/checkpoints/`, not the final iteration.

**10+ consecutive rollbacks during a run**
Usually means the Sub-Agent is producing unparseable outputs (vLLM endpoint flaking, or wrong prompt template). Check `results/<run>/evolution_log.json` for the last successful action and inspect the reasoning chain.

**Run dies mid-iteration**
The pipeline is checkpoint-resumable. Re-run the same `run_evolution.py` command — it'll pick up from the last completed iteration.

---

## Tests

**`pytest` collects but errors on import**
Almost always a missing core dependency. Re-install:

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

The full suite is mocked end-to-end (no GPU, no network, no real Gemini calls) and runs in ~2 s. If you see any test reach out over the network, file an issue — that's a regression.
