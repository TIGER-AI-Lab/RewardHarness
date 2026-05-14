"""Evaluator for RewardHarness pipeline.

Computes K-pair accuracy (K=2, 3, 4) following EditReward benchmark methodology.
Reference: https://github.com/TIGER-AI-Lab/EditReward
"""

from itertools import combinations


def evaluate_prediction(prediction: str, ground_truth: str) -> dict:
    """Evaluate a single prediction against ground truth.

    Args:
        prediction: Predicted preference ("A", "B", or "tie")
        ground_truth: Ground truth label ("A", "B", or "tie")

    Returns:
        dict with 'correct' (bool) and 'gap' (float, reserved for future use)
    """
    correct = prediction.strip().upper() == ground_truth.strip().upper()
    return {"correct": correct, "gap": 0.0}


def compute_kpair_accuracy(pair_results: list, k: int) -> dict:
    """Compute K-pair group accuracy.

    K=2: 1 pair per group, binary accuracy (n_total = n_groups)
    K=3: C(3,2)=3 pairs per group, group correct iff ALL 3 correct (n_total = n_groups)
    K=4: C(4,2)=6 pairs per group, group correct iff ALL 6 correct (n_total = n_groups)

    Args:
        pair_results: List of dicts, each with 'correct' (bool) and 'group_id'
        k: Number of candidates per group (2, 3, or 4)

    Returns:
        dict with 'accuracy' (float), 'n_correct' (int), 'n_total' (int)
    """
    if k not in (2, 3, 4):
        raise ValueError(f"k must be 2, 3, or 4, got {k}")

    pairs_per_group = len(list(combinations(range(k), 2)))  # C(k,2)

    # Group results by group_id
    groups = {}
    for r in pair_results:
        gid = r["group_id"]
        if gid not in groups:
            groups[gid] = []
        groups[gid].append(r["correct"])

    n_total = len(groups)
    n_correct = 0
    for gid, results in groups.items():
        # Group is correct only if ALL pairs in the group are correct
        if all(results):
            n_correct += 1

    accuracy = n_correct / n_total if n_total > 0 else 0.0
    return {"accuracy": accuracy, "n_correct": n_correct, "n_total": n_total}
