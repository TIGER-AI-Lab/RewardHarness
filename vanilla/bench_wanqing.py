#!/usr/bin/env python3
"""
Run bench_claude/bench_genaibench/bench_imagenhub via Wanqing API gateway.

Usage:
    python vanilla/bench_wanqing.py --model gemini-3-flash-preview --bench all
    python vanilla/bench_wanqing.py --model gemini-3.1-flash-lite-preview --bench editreward
"""
import os
import sys
import argparse

# Wanqing gateway
WQ_BASE_URL = "https://wanqing-api.corp.kuaishou.com/api/gateway/v1/endpoints"
WQ_API_KEY = "lod8673a84mjaxsdllujqkm2zoy02e77rh87"

MODEL_ENDPOINTS = {
    "gemini-3-flash-preview":        "ep-cbnh9m-1774447384961853179",
    "gemini-3.1-flash-lite-preview": "ep-drt2ei-1774447574007614467",
    "gemini-3.1-pro-preview":        "ep-uvc8z8-1774447346719855727",
    "claude-opus-4-6":               "ep-yu5i30-1774447190229324810",
    "claude-sonnet-4-6":             "ep-60book-1774447230635513394",
    "claude-haiku-4-5-20251001":     "ep-d9qbtq-1774447272953262768",
    "gpt-5-2025-08-07":              "ep-ebdtob-1774446135415679078",
}


def patch_openai(endpoint_id, model_name):
    """Monkey-patch openai.OpenAI to use wanqing gateway."""
    import openai

    _orig_init = openai.OpenAI.__init__

    def _patched_init(self, *a, **kw):
        kw["base_url"] = WQ_BASE_URL
        kw["api_key"] = WQ_API_KEY
        _orig_init(self, *a, **kw)

    openai.OpenAI.__init__ = _patched_init

    # Patch models.list to return our endpoint as available
    def _patched_list(self, *a, **kw):
        class FakeModel:
            def __init__(self, mid):
                self.id = mid
        class FakeList:
            def __init__(self):
                self.data = [FakeModel(endpoint_id), FakeModel(model_name)]
        return FakeList()

    openai.resources.models.Models.list = _patched_list


def run_bench(script_path, endpoint_id, concurrency, results_dir, max_examples=None):
    """Execute a bench script with patched args."""
    argv = [script_path, "--model", endpoint_id, "--concurrency", str(concurrency), "--results-dir", results_dir]
    if max_examples is not None:
        argv += ["--max-examples", str(max_examples)]
    sys.argv = argv

    with open(script_path) as f:
        code = f.read()

    # Execute in a clean namespace
    ns = {"__name__": "__main__", "__file__": script_path}
    exec(compile(code, script_path, "exec"), ns)


def rename_results(results_dir, endpoint_id, model_name):
    """Rename result files from endpoint_id to model name."""
    if not os.path.isdir(results_dir):
        return
    for fname in os.listdir(results_dir):
        if endpoint_id in fname:
            new_name = fname.replace(endpoint_id, model_name)
            os.rename(os.path.join(results_dir, fname), os.path.join(results_dir, new_name))
            print(f"Renamed: {fname} -> {new_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Model name")
    parser.add_argument("--bench", default="all", choices=["editreward", "genaibench", "imagenhub", "all"])
    parser.add_argument("--concurrency", type=int, default=64)
    parser.add_argument("--max-examples", type=int, default=None)
    args = parser.parse_args()

    if args.model not in MODEL_ENDPOINTS:
        print(f"Unknown model: {args.model}")
        print(f"Available: {list(MODEL_ENDPOINTS.keys())}")
        sys.exit(1)

    endpoint_id = MODEL_ENDPOINTS[args.model]
    vanilla_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(vanilla_dir, "results")

    # Remove proxy env vars (disabled)
    for k in list(os.environ):
        if False and "proxy" in k.lower():
            del os.environ[k]

    # Patch openai before importing bench scripts
    patch_openai(endpoint_id, args.model)

    bench_scripts = {
        "editreward": os.path.join(vanilla_dir, "bench_claude.py"),
        "genaibench": os.path.join(vanilla_dir, "bench_genaibench.py"),
        "imagenhub":  os.path.join(vanilla_dir, "bench_imagenhub.py"),
    }

    benches = list(bench_scripts.keys()) if args.bench == "all" else [args.bench]

    for bench in benches:
        script = bench_scripts[bench]
        print(f"\n{'='*60}")
        print(f"Running {bench} for {args.model} (endpoint={endpoint_id})")
        print(f"{'='*60}\n")

        try:
            run_bench(script, endpoint_id, args.concurrency, results_dir, args.max_examples)
        except SystemExit:
            pass
        except Exception as e:
            print(f"[ERROR] {bench}: {e}")

        #rename_results(results_dir, endpoint_id, args.model)

    print(f"\n{'='*60}")
    print(f"ALL DONE: {args.model}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
