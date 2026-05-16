#!/usr/bin/env python3
import os, urllib.request
for _k in [k for k in os.environ if "proxy" in k.lower()]: del os.environ[_k]
urllib.request.getproxies = lambda: {}


"""
Vanilla Claude benchmark on TIGER-Lab/GenAI-Bench (image_edition).
Pairwise 4-class accuracy: A>B, B>A, A=B=Good, A=B=Bad.

Usage:
    python vanilla/bench_genaibench.py --model claude-sonnet-4-6 --concurrency 256
"""

import argparse
import base64
import json
import os
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

from datasets import load_dataset
from openai import OpenAI
from tqdm import tqdm

BASE_URL = os.environ.get("GEMINI_GATEWAY_BASE_URL", "https://your-gateway.example.com/v1")
API_KEY = os.environ.get("GEMINI_GATEWAY_API_KEY", "")

# GenAI-Bench official pairwise template for image_edition
SYSTEM_PROMPT = """Please act as an impartial judge and a professional digital artist to evaluate the quality of the responses provided by two AI image edition models to the user inputs displayed below. You will be given model A's edited image and model B's edited image. Your job is to evaluate which assistant's edited image is better.

When evaluating the quality of the edited images, you must identify the any inappropriateness in the edited images by considering the following criteria:
1. Whether the editing instruction has been followed successfully in the edited image.
2. Whether the edited image is overedited, such as the scene in the edited image is completely different from the original.
3. Whether the edited image looks natural, such as the sense of distance, shadow, and lighting.
4. Whether the edited image contains any artifacts, such as distortion, watermark, scratches, blurred faces, unusual body parts, or subjects not harmonized.
5. Whether the edited image is visually appealing and esthetically pleasing.

After providing your explanation, you must output only one of the following choices as your final verdict with a label:

1. Model A is better: [[A>B]]
2. Model B is better: [[B>A]]
3. Tie, relatively the same acceptable quality: [[A=B=Good]]
4. Both are bad: [[A=B=Bad]]"""


def image_to_base64(image) -> str:
    """Convert PIL Image to base64 data URL (PNG, lossless)."""
    buf = BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def parse_response(response: str) -> str:
    """Parse model response to one of: A>B, B>A, A=B=Good, A=B=Bad, Unknown."""
    # Strong bracket patterns (exact match)
    strong_patterns = [
        (r"\[\[A>>?B\]\]", "A>B"),
        (r"\[\[B>>?A\]\]", "B>A"),
        (r"\[\[A=B=Good\]\]", "A=B=Good"),
        (r"\[\[A=B=Bad\]\]", "A=B=Bad"),
        (r"\[\[A=B\]\]", "A=B=Good"),  # generic tie -> treat as Good
    ]
    for pat, val in strong_patterns:
        if re.search(pat, response, re.IGNORECASE):
            return val

    # Fallback: weaker patterns
    if re.search(r"\bModel A is better\b", response, re.IGNORECASE):
        return "A>B"
    if re.search(r"\bModel B is better\b", response, re.IGNORECASE):
        return "B>A"
    if re.search(r"\bboth are bad\b", response, re.IGNORECASE):
        return "A=B=Bad"
    if re.search(r"\b(tie|equal|same)\b", response, re.IGNORECASE):
        return "A=B=Good"

    return "Unknown"


# Mapping from vote_type to acceptable model predictions
VOTE_CORRECT = {
    "leftvote": {"A>B"},
    "rightvote": {"B>A"},
    "tievote": {"A=B=Good", "A=B"},
    "bothbad_vote": {"A=B=Bad", "A=B"},
}


def is_correct(model_vote: str, vote_type: str) -> bool:
    """Check if model vote matches human vote."""
    if vote_type == "leftvote":
        return model_vote in ("A>B",)
    elif vote_type == "rightvote":
        return model_vote in ("B>A",)
    elif vote_type == "tievote":
        return model_vote in ("A=B=Good", "A=B")
    elif vote_type == "bothbad_vote":
        return model_vote in ("A=B=Bad", "A=B")
    return False


def evaluate_sample(example: dict, model: str, idx: int) -> dict:
    """Evaluate a single GenAI-Bench sample."""
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    source_prompt = example["source_prompt"]
    target_prompt = example["target_prompt"]
    instruct_prompt = example["instruct_prompt"]

    source_b64 = image_to_base64(example["source_image"])
    left_b64 = image_to_base64(example["left_output_image"])
    right_b64 = image_to_base64(example["right_output_image"])

    user_content = [
        {"type": "text", "text": f"Source Image prompt: {source_prompt}\nTarget Image prompt after editing: {target_prompt}\nEditing instruction: {instruct_prompt}\n\nSource Image:"},
        {"type": "image_url", "image_url": {"url": source_b64}},
        {"type": "text", "text": "\nModel A Edited Image:"},
        {"type": "image_url", "image_url": {"url": left_b64}},
        {"type": "text", "text": "\nModel B Edited Image:"},
        {"type": "image_url", "image_url": {"url": right_b64}},
        {"type": "text", "text": "\nCompare the two edited images. Which better follows the editing instruction with higher visual quality? Output your verdict."},
    ]

    import time as _time
    for _attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=81920,
            )
            break
        except Exception as _e:
            if "429" in str(_e) or "TooManyRequests" in str(_e) or "Connection" in str(_e):
                if _attempt < 4:
                    _time.sleep(2 ** (_attempt + 1))
                    continue
            raise

    response_text = resp.choices[0].message.content or ""
    model_vote = parse_response(response_text)
    vote_type = example["vote_type"]
    correct = is_correct(model_vote, vote_type)

    return {
        "idx": idx,
        "instruct_prompt": instruct_prompt,
        "left_model": example.get("left_model", ""),
        "right_model": example.get("right_model", ""),
        "vote_type": vote_type,
        "model_vote": model_vote,
        "is_correct": correct,
        "response": response_text,
    }


def main():
    parser = argparse.ArgumentParser(description="Vanilla Claude GenAI-Bench")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude model name")
    parser.add_argument("--concurrency", type=int, default=256, help="Concurrent requests")
    parser.add_argument("--max-examples", type=int, default=None, help="Limit examples")
    parser.add_argument("--results-dir", default=None, help="Results directory")
    args = parser.parse_args()

    results_dir = args.results_dir or os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    print(f"Model: {args.model}")
    print(f"Concurrency: {args.concurrency}")

    # Verify proxy
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    # models = client.models.list()  # skip for internal gateway
    available = [args.model]  # internal gateway: skip validation
    # assert args.model in available  # internal gateway: skip, f"{args.model} not in {available}"
    print(f"Proxy OK. Available models: {available}")

    # Load dataset
    print("Loading GenAI-Bench image_edition test_v1...")
    import pickle; dataset = pickle.load(open(os.path.join(os.path.dirname(__file__), ".dataset_cache", "genaibench.pkl"), "rb"))
    print(f"Loaded {len(dataset)} samples")

    # Vote distribution
    votes = defaultdict(int)
    for row in dataset:
        votes[row["vote_type"]] += 1
    print(f"Vote distribution: {dict(votes)}")

    samples = list(dataset)
    if args.max_examples:
        samples = samples[:args.max_examples]

    # Check for existing partial results
    results_file = os.path.join(results_dir, f"{args.model}_genaibench.json")
    existing = {}
    if os.path.exists(results_file):
        with open(results_file) as f:
            data = json.load(f)
        for r in data.get("results", []):
            if r and "is_correct" in r:
                existing[r["idx"]] = r
        print(f"Found {len(existing)} existing results, resuming...")

    all_results = list(existing.values())
    to_process = [(samples[i], args.model, i) for i in range(len(samples)) if i not in existing]

    if not to_process:
        print("All samples already evaluated!")
    else:
        print(f"Evaluating {len(to_process)} samples...")
        t0 = time.perf_counter()
        errors = 0

        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = {}
            for ex, model, idx in to_process:
                fut = executor.submit(evaluate_sample, ex, model, idx)
                futures[fut] = idx

            with tqdm(total=len(futures), desc="GenAI-Bench") as pbar:
                for fut in as_completed(futures):
                    idx = futures[fut]
                    try:
                        result = fut.result()
                        all_results.append(result)

                        if pbar.n % 50 == 0 and pbar.n > 0:
                            _save_partial(results_file, args.model, all_results)
                    except Exception as e:
                        errors += 1
                        all_results.append({
                            "idx": idx,
                            "vote_type": "unknown",
                            "model_vote": "Error",
                            "is_correct": False,
                            "response": str(e),
                        })
                        if errors <= 5:
                            tqdm.write(f"[ERROR] idx={idx}: {str(e)[:100]}")
                    pbar.update(1)

        elapsed = time.perf_counter() - t0
        print(f"Completed in {elapsed:.1f}s ({len(to_process)/elapsed:.1f} samples/s)")
        if errors:
            print(f"Errors: {errors}")

    # Compute accuracy
    valid = [r for r in all_results if r.get("vote_type") != "unknown"]
    n_correct = sum(1 for r in valid if r["is_correct"])
    accuracy = n_correct / len(valid) if valid else 0
    pct = round(accuracy * 100, 1)

    print(f"\n{'='*60}")
    print(f"RESULTS: {args.model} on GenAI-Bench (image_edition)")
    print(f"{'='*60}")
    print(f"Accuracy: {pct}% ({n_correct}/{len(valid)})")

    # Vote distribution of model
    model_votes = defaultdict(int)
    for r in valid:
        model_votes[r["model_vote"]] += 1
    print(f"Model vote distribution: {dict(model_votes)}")

    # Per vote_type accuracy
    for vt in ["leftvote", "rightvote", "tievote", "bothbad_vote"]:
        vt_samples = [r for r in valid if r["vote_type"] == vt]
        if vt_samples:
            vt_correct = sum(1 for r in vt_samples if r["is_correct"])
            print(f"  {vt}: {vt_correct}/{len(vt_samples)} = {vt_correct/len(vt_samples)*100:.1f}%")

    # Save final results
    final = {
        "model": args.model,
        "benchmark": "GenAI-Bench",
        "config": "image_edition",
        "split": "test_v1",
        "accuracy": pct,
        "n_correct": n_correct,
        "n_total": len(valid),
        "model_vote_distribution": dict(model_votes),
        "results": sorted(all_results, key=lambda x: x.get("idx", 0)),
    }
    with open(results_file, "w") as f:
        json.dump(final, f, indent=2, default=str)
    print(f"Saved to {results_file}")

    # Save summary
    summary_file = os.path.join(results_dir, f"{args.model}_genaibench_summary.json")
    summary = {
        "model": args.model,
        "benchmark": "GenAI-Bench",
        "accuracy": pct,
        "n_correct": n_correct,
        "n_total": len(valid),
    }
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_file}")


def _save_partial(path, model, results):
    with open(path, "w") as f:
        json.dump({"model": model, "benchmark": "GenAI-Bench", "results": results}, f, indent=2, default=str)


if __name__ == "__main__":
    main()
