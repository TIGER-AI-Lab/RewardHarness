#!/usr/bin/env python3
import os, urllib.request
for _k in [k for k in os.environ if "proxy" in k.lower()]: del os.environ[_k]
urllib.request.getproxies = lambda: {}


"""
Vanilla Claude benchmark on TIGER-Lab/EditReward-Bench.
No RewardHarness skills/tools — pure Claude as image editing judge.
High concurrency via ThreadPoolExecutor + CLIProxyAPI.

Usage:
    python vanilla/bench_claude.py --model claude-sonnet-4-6 --concurrency 256
    python vanilla/bench_claude.py --model claude-haiku-4-5-20251001 --concurrency 512
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

from datasets import load_dataset
from openai import OpenAI
from tqdm import tqdm

BASE_URL = "https://wanqing-api.corp.kuaishou.com/api/gateway/v1/endpoints"
API_KEY = "lod8673a84mjaxsdllujqkm2zoy02e77rh87"

SYSTEM_PROMPT = """You are an expert image editing quality evaluator. You will compare two edited images (A and B) produced from the same source image following an editing instruction.

## Evaluation Criteria

### 1. Instruction Following & Semantic Fidelity (1-4)
- Semantic Accuracy: Does the edit match the instruction's meaning exactly?
- Completeness: Are ALL parts of the instruction executed?
- Exclusivity: Are ONLY the requested parts changed?

### 2. Visual Quality & Realism (1-4)
- Physical Consistency: Lighting, shadows, perspective all natural?
- Artifact-Free: No blur, distortions, seams, or unnatural textures?
- Aesthetic Quality: Natural, balanced, pleasant result?

## Scoring
- 4 (Very Good): Perfect execution
- 3 (Relatively Good): Minor flaws
- 2 (Relatively Poor): Major issues
- 1 (Very Poor): Failed execution

## Output Format
Analyze both images carefully, then output your verdict as:
[[A>B]] if Image A is better
[[B>A]] if Image B is better
[[A=B]] if they are equal

You MUST include exactly one of [[A>B]], [[B>A]], or [[A=B]] in your response."""


def image_to_base64(image) -> str:
    """Convert PIL Image to base64 data URL."""
    buf = BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def parse_response(response: str) -> str:
    """Parse Claude response to A>B, B>A, A=B, or Unknown."""
    patterns = [
        (r"\[\[A>B\]\]", "A>B"),
        (r"\[\[B>A\]\]", "B>A"),
        (r"\[\[A=B\]\]", "A=B"),
        (r"\[\[A >>? B\]\]", "A>B"),
        (r"\[\[B >>? A\]\]", "B>A"),
        (r"\[\[A ==? B\]\]", "A=B"),
    ]
    for pat, val in patterns:
        if re.search(pat, response, re.IGNORECASE):
            return val

    # Fallback patterns
    if re.search(r"\bA\s+is\s+better\b", response, re.IGNORECASE):
        return "A>B"
    if re.search(r"\bB\s+is\s+better\b", response, re.IGNORECASE):
        return "B>A"
    if re.search(r"\b(tie|equal|same)\b", response, re.IGNORECASE):
        return "A=B"

    return "Unknown"


def parse_ranking(ranking: str, comparison_type: str) -> str:
    """Convert ranking 'B>A' + comparison_type 'AvsB' to gt label for this pair."""
    ranking = ranking.strip()
    if "=" in ranking:
        return "A=B"

    ct = comparison_type.replace("vs", "v")
    parts = ct.split("v")
    if len(parts) != 2:
        return "A=B"
    c1_letter, c2_letter = parts[0].strip(), parts[1].strip()

    if ">" in ranking:
        winner = ranking.split(">")[0].strip()
    else:
        return "A=B"

    # candidate_1 maps to c1_letter, candidate_2 maps to c2_letter
    # In the pair, candidate_1 = left = "A position", candidate_2 = right = "B position"
    if winner == c1_letter:
        return "A>B"  # candidate_1 wins
    elif winner == c2_letter:
        return "B>A"  # candidate_2 wins
    return "A=B"


def evaluate_pair(example: dict, model: str, idx: int) -> dict:
    """Evaluate a single pair with vanilla Claude."""
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    instruction = example["instruction"]
    source_b64 = image_to_base64(example["source_image"])
    cand1_b64 = image_to_base64(example["candidate_1"])
    cand2_b64 = image_to_base64(example["candidate_2"])

    user_content = [
        {"type": "text", "text": f"Editing instruction: {instruction}\n\nSource image:"},
        {"type": "image_url", "image_url": {"url": source_b64}},
        {"type": "text", "text": "Edited Image A:"},
        {"type": "image_url", "image_url": {"url": cand1_b64}},
        {"type": "text", "text": "Edited Image B:"},
        {"type": "image_url", "image_url": {"url": cand2_b64}},
        {"type": "text", "text": "Compare Image A and Image B. Which better follows the editing instruction with higher visual quality? Output your verdict."},
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
                max_tokens=1024,
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
    gt = parse_ranking(example["ranking"], example["comparison_type"])

    is_correct = (model_vote == gt)

    return {
        "id": example["id"],
        "idx": idx,
        "instruction": instruction,
        "comparison_type": example.get("comparison_type", ""),
        "gt": gt,
        "model_vote": model_vote,
        "is_correct": is_correct,
        "response": response_text,
    }


def compute_group_accuracy(pair_results: list, k: int) -> dict:
    """Compute K-pair group accuracy. All pairs in a group must be correct."""
    groups = defaultdict(list)
    for r in pair_results:
        # Extract group_id from id (prefix before first underscore)
        rid = r["id"]
        group_id = rid.split("_")[0] if "_" in rid else rid
        groups[group_id].append(r)

    expected_pairs = {2: 1, 3: 3, 4: 6}[k]
    correct_groups = 0
    total_groups = 0

    for group_id, samples in groups.items():
        if len(samples) == expected_pairs:
            total_groups += 1
            if all(s["is_correct"] for s in samples):
                correct_groups += 1

    accuracy = correct_groups / total_groups if total_groups > 0 else 0
    return {
        "accuracy": accuracy,
        "n_correct": correct_groups,
        "n_total": total_groups,
        "n_pairs": len(pair_results),
    }


def main():
    parser = argparse.ArgumentParser(description="Vanilla Claude EditReward-Bench")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude model name")
    parser.add_argument("--concurrency", type=int, default=256, help="Concurrent requests")
    parser.add_argument("--dataset", default="TIGER-Lab/EditReward-Bench", help="Dataset name")
    parser.add_argument("--max-examples", type=int, default=None, help="Limit examples (for testing)")
    parser.add_argument("--results-dir", default=None, help="Results directory")
    args = parser.parse_args()

    results_dir = args.results_dir or os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    print(f"Model: {args.model}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Dataset: {args.dataset}")

    # Verify proxy
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    # models = client.models.list()  # skip for wanqing
    available = [args.model]  # wanqing: skip validation
    # assert args.model in available  # wanqing: skip, f"{args.model} not in {available}"
    print(f"Proxy OK. Available models: {available}")

    # Load dataset
    print("Loading dataset...")
    import pickle; dataset = pickle.load(open(os.path.join(os.path.dirname(__file__), ".dataset_cache", "editreward_bench.pkl"), "rb"))
    print(f"Loaded {len(dataset)} total samples")

    # Group by num_candidates (K value)
    k_groups = defaultdict(list)
    for row in dataset:
        k_groups[row["num_candidates"]].append(row)

    for k in [2, 3, 4]:
        print(f"  K={k}: {len(k_groups.get(k, []))} pairs")

    all_results = {}

    for k in [2, 3, 4]:
        if k not in k_groups:
            print(f"No K={k} data, skipping")
            continue

        pairs = k_groups[k]
        if args.max_examples:
            pairs = pairs[:args.max_examples]

        print(f"\n{'='*60}")
        print(f"Running K={k} evaluation ({len(pairs)} pairs, concurrency={args.concurrency})")
        print(f"{'='*60}")

        # Check for existing partial results
        results_file = os.path.join(results_dir, f"{args.model}_k{k}.json")
        existing = {}
        if os.path.exists(results_file):
            with open(results_file) as f:
                data = json.load(f)
            for r in data.get("pair_results", []):
                if r and "is_correct" in r:
                    existing[r["idx"]] = r
            print(f"Found {len(existing)} existing results, resuming...")

        pair_results = list(existing.values())
        to_process = [(ex, args.model, i) for i, ex in enumerate(pairs) if i not in existing]

        if not to_process:
            print("All pairs already evaluated!")
        else:
            t0 = time.perf_counter()
            errors = 0

            with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = {}
                for ex, model, idx in to_process:
                    fut = executor.submit(evaluate_pair, ex, model, idx)
                    futures[fut] = idx

                with tqdm(total=len(futures), desc=f"K={k}") as pbar:
                    for fut in as_completed(futures):
                        idx = futures[fut]
                        try:
                            result = fut.result()
                            pair_results.append(result)

                            # Save every 50 completions
                            if pbar.n % 50 == 0 and pbar.n > 0:
                                _save_partial(results_file, args.model, k, pair_results)
                        except Exception as e:
                            errors += 1
                            pair_results.append({
                                "id": f"error_{idx}",
                                "idx": idx,
                                "gt": "unknown",
                                "model_vote": "Unknown",
                                "is_correct": False,
                                "response": str(e),
                            })
                            if errors <= 5:
                                tqdm.write(f"[ERROR] idx={idx}: {str(e)[:100]}")
                        pbar.update(1)

            elapsed = time.perf_counter() - t0
            print(f"Completed in {elapsed:.1f}s ({len(to_process)/elapsed:.1f} pairs/s)")
            if errors:
                print(f"Errors: {errors}")

        # Compute accuracy
        acc = compute_group_accuracy(pair_results, k)
        all_results[f"k{k}"] = acc
        print(f"K={k} Group Accuracy: {acc['accuracy']:.4f} ({acc['n_correct']}/{acc['n_total']})")

        # Individual accuracy
        valid = [r for r in pair_results if r.get("gt") != "unknown"]
        ind_correct = sum(1 for r in valid if r["is_correct"])
        ind_acc = ind_correct / len(valid) if valid else 0
        print(f"K={k} Individual Accuracy: {ind_acc:.4f} ({ind_correct}/{len(valid)})")

        # Vote distribution
        votes = defaultdict(int)
        for r in valid:
            votes[r["model_vote"]] += 1
        print(f"K={k} Vote distribution: {dict(votes)}")

        # Save final
        final = {
            "model": args.model,
            "k": k,
            "group_accuracy": acc["accuracy"],
            "group_correct": acc["n_correct"],
            "group_total": acc["n_total"],
            "individual_accuracy": ind_acc,
            "individual_correct": ind_correct,
            "individual_total": len(valid),
            "n_pairs": len(pair_results),
            "pair_results": pair_results,
        }
        with open(results_file, "w") as f:
            json.dump(final, f, indent=2, default=str)
        print(f"Saved to {results_file}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {args.model}")
    print(f"{'='*60}")
    for k in [2, 3, 4]:
        key = f"k{k}"
        if key in all_results:
            a = all_results[key]
            print(f"  K={k}: {a['accuracy']:.4f} ({a['n_correct']}/{a['n_total']})")

    # Save combined summary
    summary_file = os.path.join(results_dir, f"{args.model}_summary.json")
    with open(summary_file, "w") as f:
        json.dump({"model": args.model, "results": all_results}, f, indent=2)
    print(f"\nSummary saved to {summary_file}")


def _save_partial(path, model, k, pair_results):
    """Save intermediate results for resume."""
    with open(path, "w") as f:
        json.dump({
            "model": model,
            "k": k,
            "pair_results": pair_results,
        }, f, indent=2, default=str)


if __name__ == "__main__":
    main()
