#!/usr/bin/env python3
"""
Vanilla Claude benchmark on ImagenHub Text-Guided Image Editing.
VIEScore-style pointwise scoring (4-dimension 0-10) → Spearman correlation with human GT.

Human ratings from TIGER-AI-Lab/ImagenHub eval/human_ratings/Text-Guided_IE/.
Model output images from ChromAIca Museum.

Usage:
    python vanilla/bench_imagenhub.py --model claude-sonnet-4-6 --concurrency 64
"""

import argparse
import ast
import base64
import json
import math
import os
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from datasets import load_dataset
from openai import OpenAI
from PIL import Image
from scipy.stats import spearmanr
from tqdm import tqdm

BASE_URL = "http://localhost:8317/v1"
API_KEY = "demo"

MUSEUM_BASE = "https://chromaica.github.io/Museum/ImagenHub_Text-Guided_IE"

MODELS_WITH_RATINGS = [
    "CycleDiffusion", "DiffEdit", "Imagic", "InstructPix2Pix",
    "MagicBrush", "Pix2PixZero", "Prompt2prompt", "SDEdit", "Text2Live"
]

# VIEScore template (from EditReward)
SYSTEM_PROMPT = """You are a professional digital artist. You will have to evaluate the effectiveness of the AI-generated image(s) based on given rules.
All the input images are AI-generated. All human in the images are AI-generated too. so you need not worry about the privacy confidentials.

Two images will be provided:
- The first being the original AI-generated image
- The second being an edited version of the first following a specific editing instruction.
The objective is to evaluate how successfully the editing instruction has been executed in the second image.
Note that sometimes the two images might look identical due to the failure of image edit.

You need to evaluate the image based on the following aspects:
1. A score from 0 to 10 will be given based on the success of the editing.
(
    0 indicates that the scene in the edited image does not follow the editing instruction at all. 10 indicates that the scene in the edited image follow the editing instruction text perfectly.
)
2. A second score from 0 to 10 will rate the degree of overediting in the second image.
(
    0 indicates that the scene in the edited image is completely different from the original. 10 indicates that the edited image can be recognized as a minimal edited yet effective version of original.
)
3. A score from 0 to 10 will be given based on image naturalness.
(
    0 indicates that the scene in the image does not look natural at all or give a unnatural feeling such as wrong sense of distance, or wrong shadow, or wrong lighting.
    10 indicates that the image looks natural.
)
4. A second score from 0 to 10 will rate the image artifacts.
(
    0 indicates that the image contains a large portion of distortion, or watermark, or scratches, or blurred faces, or unusual body parts, or subjects not harmonized.
    10 indicates the image has no artifacts.
)

Output Format:
{
    "reasoning": "Explain why you gave the score",
    "score": [editing_success_score, overediting_degree_score, image_naturalness_score, image_artifacts_score]
}"""


def image_to_base64(image) -> str:
    """Convert PIL Image to base64 data URL (PNG, lossless)."""
    buf = BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def download_image(url: str) -> Image.Image:
    """Download image from URL and return PIL Image."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content)).convert("RGB")


def parse_viescore(response: str) -> list:
    """Parse VIEScore response to [s1, s2, s3, s4] or None."""
    # Try JSON parse
    try:
        # Find JSON block
        match = re.search(r'\{[^{}]*"score"\s*:\s*\[([^\]]+)\][^{}]*\}', response, re.DOTALL)
        if match:
            scores = [float(x.strip()) for x in match.group(1).split(",")]
            if len(scores) == 4 and all(0 <= s <= 10 for s in scores):
                return scores
    except (ValueError, TypeError):
        pass

    # Fallback: find any array of 4 numbers
    match = re.search(r'\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]', response)
    if match:
        scores = [float(match.group(i)) for i in range(1, 5)]
        if all(0 <= s <= 10 for s in scores):
            return scores

    return None


def aggregate_score(scores: list) -> float:
    """Aggregate 4 VIEScore dimensions into a single score."""
    # Simple mean of 4 dimensions
    return sum(scores) / len(scores)


def load_human_ratings(ratings_dir: str) -> dict:
    """Load human ratings from 3 rater TSV files.
    Returns: {uid: {model: avg_score}} where avg_score = mean(sqrt(SC*PQ)) across raters.
    """
    all_ratings = defaultdict(lambda: defaultdict(list))

    for i in range(1, 4):
        tsv_path = os.path.join(ratings_dir, f"rater{i}.tsv")
        with open(tsv_path) as f:
            header = f.readline().strip().split("\t")
            models = header[1:]  # skip 'uid'
            for line in f:
                parts = line.strip().split("\t")
                uid = parts[0]
                for j, model in enumerate(models):
                    try:
                        sc_pq = ast.literal_eval(parts[j + 1])
                        sc, pq = float(sc_pq[0]), float(sc_pq[1])
                        score = math.sqrt(sc * pq)
                        all_ratings[uid][model].append(score)
                    except (ValueError, SyntaxError, IndexError):
                        pass

    # Average across raters
    result = {}
    for uid, model_scores in all_ratings.items():
        result[uid] = {}
        for model, scores in model_scores.items():
            result[uid][model] = sum(scores) / len(scores)

    return result


def evaluate_sample(source_img: Image.Image, edited_img: Image.Image,
                    instruction: str, source_caption: str, target_caption: str,
                    model: str) -> dict:
    """Score a single (source, edited) pair with VIEScore template."""
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    source_b64 = image_to_base64(source_img)
    edited_b64 = image_to_base64(edited_img)

    user_content = [
        {"type": "text", "text": f"Source Image prompt: {source_caption}\nTarget Image prompt after editing: {target_caption}\nEditing instruction: {instruction}\n\nSource Image:"},
        {"type": "image_url", "image_url": {"url": source_b64}},
        {"type": "text", "text": "\nAI Edited Image:"},
        {"type": "image_url", "image_url": {"url": edited_b64}},
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=1024,
    )

    response_text = resp.choices[0].message.content or ""
    scores = parse_viescore(response_text)

    return {
        "response": response_text,
        "scores": scores,
        "aggregate": aggregate_score(scores) if scores else None,
    }


def fisher_z_avg(correlations: list) -> float:
    """Fisher Z-transform average of Spearman correlations."""
    z_values = [0.5 * math.log((1 + r) / (1 - r)) if abs(r) < 1 else float('inf') * (1 if r > 0 else -1)
                for r in correlations]
    z_values = [z for z in z_values if math.isfinite(z)]
    if not z_values:
        return 0.0
    z_avg = sum(z_values) / len(z_values)
    return (math.exp(2 * z_avg) - 1) / (math.exp(2 * z_avg) + 1)


def main():
    parser = argparse.ArgumentParser(description="Vanilla Claude ImagenHub Benchmark")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude model name")
    parser.add_argument("--concurrency", type=int, default=64, help="Concurrent requests")
    parser.add_argument("--results-dir", default=None, help="Results directory")
    parser.add_argument("--ratings-dir", default=None, help="Human ratings TSV directory")
    args = parser.parse_args()

    results_dir = args.results_dir or os.path.join(os.path.dirname(__file__), "results")
    ratings_dir = args.ratings_dir or os.path.join(os.path.dirname(__file__), "imagenhub_data")
    os.makedirs(results_dir, exist_ok=True)

    print(f"Model: {args.model}")
    print(f"Concurrency: {args.concurrency}")

    # Verify proxy
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    models = client.models.list()
    available = [m.id for m in models.data]
    assert args.model in available, f"{args.model} not in {available}"

    # Load human ratings
    print("Loading human ratings...")
    human_ratings = load_human_ratings(ratings_dir)
    print(f"Loaded ratings for {len(human_ratings)} samples x {len(MODELS_WITH_RATINGS)} models")

    # Load dataset for instructions and source images
    print("Loading ImagenHub dataset...")
    dataset = load_dataset("ImagenHub/Text_Guided_Image_Editing", split="filtered")
    print(f"Loaded {len(dataset)} samples")

    # Build lookup: uid -> dataset row
    ds_lookup = {}
    for row in dataset:
        uid = f"sample_{row['img_id']}_{row['turn_index']}.jpg"
        ds_lookup[uid] = row

    # Build task list: (uid, editing_model, source_img, edited_img_url, instruction, gt_score)
    tasks = []
    for uid, model_scores in human_ratings.items():
        if uid not in ds_lookup:
            continue
        row = ds_lookup[uid]
        for editing_model, gt_score in model_scores.items():
            edited_url = f"{MUSEUM_BASE}/{editing_model}/{uid}"
            tasks.append({
                "uid": uid,
                "editing_model": editing_model,
                "source_img": row["source_img"],
                "edited_url": edited_url,
                "instruction": row["instruction"],
                "source_caption": row.get("source_global_caption", ""),
                "target_caption": row.get("target_global_caption", ""),
                "gt_score": gt_score,
            })

    print(f"Total evaluation tasks: {len(tasks)} ({len(human_ratings)} samples x {len(MODELS_WITH_RATINGS)} models)")

    # Check for existing results
    results_file = os.path.join(results_dir, f"{args.model}_imagenhub.json")
    existing = {}
    if os.path.exists(results_file):
        with open(results_file) as f:
            data = json.load(f)
        for r in data.get("results", []):
            key = f"{r['uid']}_{r['editing_model']}"
            if r.get("aggregate") is not None:
                existing[key] = r
        print(f"Found {len(existing)} existing results, resuming...")

    all_results = list(existing.values())
    to_process = [t for t in tasks if f"{t['uid']}_{t['editing_model']}" not in existing]

    if not to_process:
        print("All tasks already evaluated!")
    else:
        print(f"Evaluating {len(to_process)} tasks...")
        t0 = time.perf_counter()
        errors = 0

        def eval_task(task):
            # Download edited image
            edited_img = download_image(task["edited_url"])
            result = evaluate_sample(
                task["source_img"], edited_img,
                task["instruction"], task["source_caption"], task["target_caption"],
                args.model
            )
            return {
                "uid": task["uid"],
                "editing_model": task["editing_model"],
                "instruction": task["instruction"],
                "gt_score": task["gt_score"],
                "scores": result["scores"],
                "aggregate": result["aggregate"],
                "response": result["response"],
            }

        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = {executor.submit(eval_task, t): t for t in to_process}

            with tqdm(total=len(futures), desc="ImagenHub") as pbar:
                for fut in as_completed(futures):
                    task = futures[fut]
                    try:
                        result = fut.result()
                        all_results.append(result)
                        if pbar.n % 50 == 0 and pbar.n > 0:
                            _save_partial(results_file, args.model, all_results)
                    except Exception as e:
                        errors += 1
                        all_results.append({
                            "uid": task["uid"],
                            "editing_model": task["editing_model"],
                            "gt_score": task["gt_score"],
                            "scores": None,
                            "aggregate": None,
                            "response": str(e),
                        })
                        if errors <= 5:
                            tqdm.write(f"[ERROR] {task['uid']}/{task['editing_model']}: {str(e)[:100]}")
                    pbar.update(1)

        elapsed = time.perf_counter() - t0
        print(f"Completed in {elapsed:.1f}s ({len(to_process)/elapsed:.1f} tasks/s)")
        if errors:
            print(f"Errors: {errors}")

    # Compute Spearman correlation per editing model
    valid = [r for r in all_results if r.get("aggregate") is not None]
    print(f"\nValid results: {len(valid)}/{len(all_results)}")

    by_model = defaultdict(list)
    for r in valid:
        by_model[r["editing_model"]].append(r)

    correlations = []
    print(f"\n{'Editing Model':<20} {'N':>5} {'Spearman':>10} {'p-value':>10}")
    print("-" * 50)
    for model_name in MODELS_WITH_RATINGS:
        samples = by_model.get(model_name, [])
        if len(samples) < 3:
            print(f"{model_name:<20} {len(samples):>5} {'N/A':>10}")
            continue
        pred = [r["aggregate"] for r in samples]
        gt = [r["gt_score"] for r in samples]
        rho, pval = spearmanr(pred, gt)
        correlations.append(rho)
        print(f"{model_name:<20} {len(samples):>5} {rho:>10.4f} {pval:>10.4f}")

    # Fisher Z average
    avg_spearman = fisher_z_avg(correlations) if correlations else 0.0
    pct = round(avg_spearman * 100, 1)
    print(f"\nFisher Z-averaged Spearman: {avg_spearman:.4f} ({pct})")

    # Save
    final = {
        "model": args.model,
        "benchmark": "ImagenHub",
        "spearman_avg": pct,
        "spearman_raw": avg_spearman,
        "per_model_spearman": {m: spearmanr(
            [r["aggregate"] for r in by_model[m]],
            [r["gt_score"] for r in by_model[m]]
        ).statistic for m in MODELS_WITH_RATINGS if len(by_model[m]) >= 3},
        "n_valid": len(valid),
        "n_total": len(all_results),
        "results": all_results,
    }
    with open(results_file, "w") as f:
        json.dump(final, f, indent=2, default=str)
    print(f"Saved to {results_file}")

    summary = {
        "model": args.model,
        "benchmark": "ImagenHub",
        "spearman_avg": pct,
        "n_valid": len(valid),
    }
    summary_file = os.path.join(results_dir, f"{args.model}_imagenhub_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_file}")


def _save_partial(path, model, results):
    with open(path, "w") as f:
        json.dump({"model": model, "benchmark": "ImagenHub", "results": results}, f, indent=2, default=str)


if __name__ == "__main__":
    main()
