"""Unit tests for Evaluator."""

import pytest
from src.evaluator import evaluate_prediction, compute_kpair_accuracy


class TestEvaluatePrediction:
    def test_correct_a(self):
        assert evaluate_prediction("A", "A")["correct"] is True

    def test_correct_b(self):
        assert evaluate_prediction("B", "B")["correct"] is True

    def test_correct_tie(self):
        assert evaluate_prediction("tie", "tie")["correct"] is True

    def test_incorrect_a_vs_b(self):
        assert evaluate_prediction("A", "B")["correct"] is False

    def test_incorrect_tie_vs_a(self):
        assert evaluate_prediction("tie", "A")["correct"] is False

    def test_case_insensitive(self):
        assert evaluate_prediction("a", "A")["correct"] is True
        assert evaluate_prediction("TIE", "tie")["correct"] is True

    def test_whitespace_handling(self):
        assert evaluate_prediction(" A ", "A")["correct"] is True


class TestKPairAccuracy:
    def test_k2_all_correct(self):
        results = [
            {"group_id": 0, "correct": True},
            {"group_id": 1, "correct": True},
            {"group_id": 2, "correct": True},
        ]
        acc = compute_kpair_accuracy(results, k=2)
        assert acc["accuracy"] == 1.0
        assert acc["n_correct"] == 3
        assert acc["n_total"] == 3

    def test_k2_half_correct(self):
        results = [
            {"group_id": 0, "correct": True},
            {"group_id": 1, "correct": False},
        ]
        acc = compute_kpair_accuracy(results, k=2)
        assert acc["accuracy"] == 0.5
        assert acc["n_correct"] == 1
        assert acc["n_total"] == 2

    def test_k3_all_pairs_correct(self):
        # K=3: C(3,2)=3 pairs per group, ALL must be correct
        results = [
            {"group_id": 0, "correct": True},
            {"group_id": 0, "correct": True},
            {"group_id": 0, "correct": True},
        ]
        acc = compute_kpair_accuracy(results, k=3)
        assert acc["accuracy"] == 1.0
        assert acc["n_correct"] == 1

    def test_k3_one_pair_wrong(self):
        # One wrong pair in group -> group incorrect
        results = [
            {"group_id": 0, "correct": True},
            {"group_id": 0, "correct": True},
            {"group_id": 0, "correct": False},
        ]
        acc = compute_kpair_accuracy(results, k=3)
        assert acc["accuracy"] == 0.0
        assert acc["n_correct"] == 0

    def test_k4_all_correct(self):
        # K=4: C(4,2)=6 pairs per group
        results = [{"group_id": 0, "correct": True} for _ in range(6)]
        acc = compute_kpair_accuracy(results, k=4)
        assert acc["accuracy"] == 1.0

    def test_k4_one_wrong(self):
        results = [{"group_id": 0, "correct": True} for _ in range(5)]
        results.append({"group_id": 0, "correct": False})
        acc = compute_kpair_accuracy(results, k=4)
        assert acc["accuracy"] == 0.0

    def test_k2_multiple_groups(self):
        results = [
            {"group_id": 0, "correct": True},
            {"group_id": 1, "correct": False},
            {"group_id": 2, "correct": True},
            {"group_id": 3, "correct": True},
        ]
        acc = compute_kpair_accuracy(results, k=2)
        assert acc["accuracy"] == 0.75
        assert acc["n_correct"] == 3
        assert acc["n_total"] == 4

    def test_k2_tie_cases(self):
        # K=2: two groups, each with 1 pair. Both correct -> 50/50 tie not possible
        # at group level, but we test the boundary: 2 groups, 1 correct each side
        results = [
            {"group_id": 0, "correct": True},
            {"group_id": 1, "correct": False},
        ]
        acc = compute_kpair_accuracy(results, k=2)
        assert acc["accuracy"] == 0.5
        assert acc["n_correct"] == 1
        assert acc["n_total"] == 2

    def test_k3_tie_cases(self):
        # Two groups: group 0 all correct, group 1 has one wrong
        results = [
            {"group_id": 0, "correct": True},
            {"group_id": 0, "correct": True},
            {"group_id": 0, "correct": True},
            {"group_id": 1, "correct": True},
            {"group_id": 1, "correct": False},
            {"group_id": 1, "correct": True},
        ]
        acc = compute_kpair_accuracy(results, k=3)
        assert acc["accuracy"] == 0.5
        assert acc["n_correct"] == 1
        assert acc["n_total"] == 2

    def test_k4_tie_cases(self):
        # K=4: C(4,2)=6 pairs per group. Two groups: group 0 all correct,
        # group 1 has one wrong pair out of 6 -> group 1 fails
        results_g0 = [{"group_id": 0, "correct": True} for _ in range(6)]
        results_g1 = [{"group_id": 1, "correct": True} for _ in range(5)]
        results_g1.append({"group_id": 1, "correct": False})
        acc = compute_kpair_accuracy(results_g0 + results_g1, k=4)
        assert acc["accuracy"] == 0.5
        assert acc["n_correct"] == 1
        assert acc["n_total"] == 2

    def test_empty_results(self):
        acc = compute_kpair_accuracy([], k=2)
        assert acc["accuracy"] == 0.0
        assert acc["n_total"] == 0

    def test_invalid_k(self):
        with pytest.raises(ValueError):
            compute_kpair_accuracy([], k=5)
