#!/usr/bin/env python3
"""Run EditReward-Bench evaluation with the evolved Library.

Loads the benchmark dataset, runs inference using the evolved Skills/Tools library,
and computes K=2/3/4 accuracy. NO library updates — read-only evaluation.

Usage:
    python scripts/run_benchmark.py --config configs/default.yaml
"""

import argparse
import json
import os
import sys
import base64
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

import yaml
from datasets import load_dataset
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.library import Library
from src.router import Router
from src.sub_agent import SubAgent
from src.endpoint_pool import EndpointPool
from src.evaluator import evaluate_prediction, compute_kpair_accuracy


def image_to_base64(image) -> str:
    """Convert PIL Image to base64 string."""
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def parse_ranking(ranking: str, comparison_type: str) -> str:
    """Convert ranking like 'B>A' + comparison_type 'AvsB' to 'A'/'B'/'tie'.

    In comparison_type, the first letter = candidate_1, second letter = candidate_2.
    If the winner matches candidate_1's letter → 'A', candidate_2's → 'B'.
    """
    ranking = ranking.strip()

    # Handle tie
    if "=" in ranking:
        return "tie"

    # Parse comparison_type to get candidate letters
    ct = comparison_type.replace("vs", "v")  # normalize "AvsB" → "AvB"
    parts = ct.split("v")
    if len(parts) != 2:
        return "tie"
    c1_letter, c2_letter = parts[0].strip(), parts[1].strip()

    # Parse ranking to get winner
    if ">" in ranking:
        winner = ranking.split(">")[0].strip()
    else:
        return "tie"

    if winner == c1_letter:
        return "A"
    elif winner == c2_letter:
        return "B"
    return "tie"


def evaluate_pair(sub_agent, router, example):
    """Evaluate a single pair comparison (read-only, no library writes)."""
    prompt = example["instruction"]
    skill_context = router.prepare_context(prompt)

    source_b64 = image_to_base64(example["source_image"])
    edited_a_b64 = image_to_base64(example["candidate_1"])
    edited_b_b64 = image_to_base64(example["candidate_2"])

    result = sub_agent.evaluate(
        source_img=source_b64,
        edited_A=edited_a_b64,
        edited_B=edited_b_b64,
        prompt=prompt,
        skill_context=skill_context
    )

    gt = parse_ranking(example["ranking"], example["comparison_type"])
    pred = result.get("preference", "tie")
    eval_result = evaluate_prediction(pred, gt)

    return {
        "group_id": example["id"],
        "prompt": prompt,
        "gt": gt,
        "prediction": pred,
        "correct": eval_result["correct"],
        "reasoning_chain": result.get("chain", ""),
        "scores": {
            "score_A_instruction": result.get("score_A_instruction"),
            "score_A_quality": result.get("score_A_quality"),
            "score_B_instruction": result.get("score_B_instruction"),
            "score_B_quality": result.get("score_B_quality"),
        }
    }


def run_benchmark(config: dict, library_dir: str = None, results_dir: str = None):
    """Run full benchmark evaluation."""
    # Setup
    lib_dir = library_dir or os.path.join(PROJECT_ROOT, "src", "library")
    res_dir = results_dir or os.path.join(PROJECT_ROOT, "results")
    library = Library(lib_dir)
    router = Router(library, model=config["gemini"]["model"])

    endpoints_file = os.path.join(PROJECT_ROOT, "configs", "endpoints.txt")
    pool = EndpointPool(endpoints_file=endpoints_file)
    sub_agent = SubAgent(library=library, endpoint_pool=pool)

    max_workers = config.get("benchmark", {}).get("max_workers", 128)

    # Load benchmark dataset
    print("Loading TIGER-Lab/EditReward-Bench...")
    dataset = load_dataset(config["benchmark"]["dataset"], split="train")

    # Group by num_candidates (K value)
    k_groups = defaultdict(list)
    for row in dataset:
        k_groups[row["num_candidates"]].append(row)

    results = {}

    for k in [2, 3, 4]:
        if k not in k_groups:
            print(f"No K={k} examples found, skipping")
            continue

        pairs = k_groups[k]
        print(f"\nRunning K={k} evaluation ({len(pairs)} pairs)...")

        pair_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for idx, example in enumerate(pairs):
                future = executor.submit(evaluate_pair, sub_agent, router, example)
                futures[future] = idx

            for future in tqdm(as_completed(futures), total=len(futures), desc=f"K={k}"):
                try:
                    result = future.result()
                    pair_results.append(result)
                except Exception as e:
                    idx = futures[future]
                    print(f"Error on example {idx}: {e}")
                    pair_results.append({
                        "group_id": f"error_{idx}",
                        "correct": False,
                        "prediction": "error",
                        "gt": "unknown"
                    })

        accuracy = compute_kpair_accuracy(pair_results, k=k)
        results[f"k{k}"] = {
            "accuracy": accuracy["accuracy"],
            "n_correct": accuracy["n_correct"],
            "n_total": accuracy["n_total"],
            "n_pairs": len(pair_results),
            "pair_results": pair_results
        }
        print(f"K={k} accuracy: {accuracy['accuracy']:.4f} ({accuracy['n_correct']}/{accuracy['n_total']})")

    # Save results
    results_path = os.path.join(res_dir, "benchmark_results.json")
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to {results_path}")
    for k in [2, 3, 4]:
        key = f"k{k}"
        if key in results:
            print(f"K={k}: {results[key]['accuracy']:.4f} ({results[key]['n_correct']}/{results[key]['n_total']})")

    return results


def main():
    parser = argparse.ArgumentParser(description="Run EditReward-Bench evaluation")
    parser.add_argument("--config", default="configs/default.yaml", help="Config file path")
    parser.add_argument("--library-dir", default=None, help="Path to evolved library directory")
    parser.add_argument("--results-dir", default=None, help="Path to results directory")
    args = parser.parse_args()

    config_path = os.path.join(PROJECT_ROOT, args.config) if not os.path.isabs(args.config) else args.config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    run_benchmark(config, args.library_dir, args.results_dir)


if __name__ == "__main__":
    main()
