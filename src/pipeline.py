"""Self-Evolution Pipeline for RewardHarness.

Orchestrates iterative improvement of Skills and Tools libraries
through chain analysis of Sub-Agent predictions.
"""

import base64
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from src.library import Library
from src.router import Router
from src.sub_agent import SubAgent
from src.evaluator import evaluate_prediction, compute_kpair_accuracy
from src.chain_analyzer import ChainAnalyzer
from src.evolver import Evolver
from src.endpoint_pool import EndpointPool

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def image_to_base64(image) -> str:
    """Convert PIL Image to base64 string."""
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class SelfEvolutionPipeline:
    def __init__(self, config: dict, library_dir: str = None, results_dir: str = None):
        """Initialize pipeline.

        Args:
            config: parsed YAML config dict
            library_dir: path to library directory (default: src/library/)
            results_dir: path to results directory (default: results/)
        """
        train_dataset = config["evolution"]["train_dataset"]
        assert "EditReward-Bench" not in train_dataset, \
            "Benchmark data must NOT be used during evolution!"

        self.config = config
        self.lib_dir = library_dir or os.path.join(PROJECT_ROOT, "src", "library")
        self.library = Library(self.lib_dir)
        self.router = Router(self.library, model=config["gemini"]["model"])

        endpoints_file = os.path.join(PROJECT_ROOT, "configs", "endpoints.txt")
        self.endpoint_pool = EndpointPool(endpoints_file=endpoints_file)
        self.sub_agent = SubAgent(library=self.library, endpoint_pool=self.endpoint_pool)
        self.chain_analyzer = ChainAnalyzer(model=config["gemini"]["model"])
        self.evolver = Evolver(self.library, self.endpoint_pool)

        self.max_workers = config["evolution"].get("batch_concurrent", 128)
        self.results_dir = results_dir or os.path.join(PROJECT_ROOT, "results")
        self.checkpoint_dir = os.path.join(self.results_dir, "checkpoints")

    @staticmethod
    def _map_vote_type(vote_type: str) -> str:
        """Map HF dataset vote_type to evaluator format (A/B/tie)."""
        vt = vote_type.strip().lower()
        if vt == "leftvote":
            return "A"
        elif vt == "rightvote":
            return "B"
        return "tie"

    def _prepare_examples(self, dataset_split) -> list:
        """Convert HF dataset split to list of dicts with base64 images."""
        examples = []
        for idx, row in enumerate(dataset_split):
            examples.append({
                "source_img": image_to_base64(row["source_image"]),
                "edited_A": image_to_base64(row["left_image"]),
                "edited_B": image_to_base64(row["right_image"]),
                "prompt": row["instruction"],
                "gt": self._map_vote_type(row["vote_type"]),
                "group_id": idx,
            })
        return examples

    def _augment_with_swaps(self, examples: list) -> list:
        """Double dataset by swapping A/B positions and flipping labels.

        Forces evolution to learn position-invariant skills.
        """
        augmented = list(examples)
        for ex in examples:
            swapped = dict(ex)
            swapped["edited_A"] = ex["edited_B"]
            swapped["edited_B"] = ex["edited_A"]
            if ex["gt"] == "A":
                swapped["gt"] = "B"
            elif ex["gt"] == "B":
                swapped["gt"] = "A"
            # tie stays tie
            swapped["group_id"] = f"{ex['group_id']}_swap"
            augmented.append(swapped)
        return augmented

    def _prune_library(self, val_split: list) -> dict:
        """Leave-one-out ablation pruning on the val set.

        For each skill/tool: temporarily remove it and re-run val.
        If val_acc >= baseline_acc, the entry is harmful or neutral — remove it.

        Returns:
            dict with pruned_skills and pruned_tools lists
        """
        summaries = self.library.get_all_summaries()
        all_entries = (
            [(s["name"], "skill") for s in summaries["skills"]] +
            [(t["name"], "tool") for t in summaries["tools"]]
        )

        if not all_entries:
            return {"pruned_skills": [], "pruned_tools": []}

        # Baseline val accuracy with full library
        logger.info("Prune: running baseline val with full library...")
        baseline_results = self.run_iteration(val_split)
        baseline_acc = compute_kpair_accuracy(baseline_results, k=2)["accuracy"]
        logger.info(f"Prune baseline val_acc: {baseline_acc:.4f}")

        to_prune = []

        for name, entry_type in all_entries:
            # Snapshot, remove entry, run val, restore
            snap = self.library.snapshot()
            try:
                if entry_type == "skill":
                    self.library.delete_skill(name)
                else:
                    self.library.delete_tool(name)

                ablated_results = self.run_iteration(val_split)
                ablated_acc = compute_kpair_accuracy(ablated_results, k=2)["accuracy"]
                logger.info(f"Prune ablation: removing '{name}' ({entry_type}) -> "
                           f"val_acc {ablated_acc:.4f} (baseline {baseline_acc:.4f})")

                if ablated_acc >= baseline_acc:
                    to_prune.append((name, entry_type, ablated_acc))
            except Exception as e:
                logger.warning(f"Prune ablation failed for '{name}': {e}")
            finally:
                self.library.restore(snap)

        # Apply pruning (re-snapshot first, then remove all harmful entries)
        pruned_skills = []
        pruned_tools = []
        for name, entry_type, ablated_acc in to_prune:
            try:
                if entry_type == "skill":
                    self.library.delete_skill(name)
                    pruned_skills.append(name)
                else:
                    self.library.delete_tool(name)
                    pruned_tools.append(name)
                logger.info(f"Pruned '{name}' ({entry_type}): "
                           f"ablated_acc={ablated_acc:.4f} >= baseline={baseline_acc:.4f}")
            except Exception as e:
                logger.warning(f"Failed to prune '{name}': {e}")

        logger.info(f"Pruning complete: removed {len(pruned_skills)} skills, "
                   f"{len(pruned_tools)} tools")
        return {"pruned_skills": pruned_skills, "pruned_tools": pruned_tools}

    def run_iteration(self, examples: list) -> list:
        """Run one iteration: Router -> SubAgent -> Evaluator.

        Args:
            examples: list of dicts with source_img, edited_A, edited_B, prompt, gt, group_id

        Returns:
            list of result dicts with prediction, correct, reasoning_chain, etc.
        """
        # 1. Per-example routing (parallel Gemini calls, capped to avoid 429)
        with ThreadPoolExecutor(max_workers=min(len(examples), 8)) as pool:
            skill_contexts = list(pool.map(
                lambda ex: self.router.prepare_context(ex["prompt"]), examples))

        # 2. Batch evaluate
        predictions = self.sub_agent.batch_evaluate(examples, skill_contexts,
                                                      max_workers=self.max_workers)

        # 3. Compare with GT
        results = []
        for ex, pred in zip(examples, predictions):
            eval_result = evaluate_prediction(pred.get("preference", "tie"), ex["gt"])
            results.append({
                "group_id": ex["group_id"],
                "prompt": ex["prompt"],
                "gt": ex["gt"],
                "prediction": pred.get("preference", "tie"),
                "correct": eval_result["correct"],
                "reasoning_chain": pred.get("chain", ""),
                "scores": {
                    "score_A_instruction": pred.get("score_A_instruction"),
                    "score_A_quality": pred.get("score_A_quality"),
                    "score_B_instruction": pred.get("score_B_instruction"),
                    "score_B_quality": pred.get("score_B_quality"),
                },
                "reasoning": pred.get("reasoning", ""),
            })

        return results

    def _checkpoint(self, iteration: int, snap: dict, best_val_acc: float,
                    train_acc: float = None, signals: dict = None,
                    val_acc_after_skills: float = None,
                    val_acc_after_tools: float = None):
        """Save checkpoint for an iteration."""
        iter_dir = os.path.join(self.checkpoint_dir, f"iter_{iteration}")
        os.makedirs(iter_dir, exist_ok=True)

        # Save registry
        with open(os.path.join(iter_dir, "registry.json"), 'w') as f:
            json.dump(snap["registry"], f, indent=2)

        # Save all SKILL.md files
        for name, content in snap.get("skills_content", {}).items():
            skill_dir = os.path.join(iter_dir, "skills", name)
            os.makedirs(skill_dir, exist_ok=True)
            with open(os.path.join(skill_dir, "SKILL.md"), 'w') as f:
                f.write(content)

        for name, content in snap.get("tools_content", {}).items():
            tool_dir = os.path.join(iter_dir, "tools", name)
            os.makedirs(tool_dir, exist_ok=True)
            with open(os.path.join(tool_dir, "SKILL.md"), 'w') as f:
                f.write(content)

        # Save metadata – always save best_val_acc so resume loads the correct baseline
        metadata = {
            "iteration": iteration,
            "best_val_acc": best_val_acc,
            "val_acc": best_val_acc,  # backward compat
            "val_acc_after_skills": val_acc_after_skills,
            "val_acc_after_tools": val_acc_after_tools,
            "train_acc": train_acc,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "n_skills": len(snap.get("skills_content", {})),
            "n_tools": len(snap.get("tools_content", {})),
        }
        if signals:
            metadata["analysis_summary"] = signals.get("analysis_summary", "")
        with open(os.path.join(iter_dir, "metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_checkpoint(self, iter_dir: str) -> tuple:
        """Load checkpoint and restore Library state.

        Returns:
            (metadata dict, snapshot dict)
        """
        with open(os.path.join(iter_dir, "metadata.json")) as f:
            metadata = json.load(f)

        with open(os.path.join(iter_dir, "registry.json")) as f:
            registry = json.load(f)

        snap = {"registry": registry, "skills_content": {}, "tools_content": {}}

        skills_dir = os.path.join(iter_dir, "skills")
        if os.path.exists(skills_dir):
            for name in os.listdir(skills_dir):
                skill_file = os.path.join(skills_dir, name, "SKILL.md")
                if os.path.exists(skill_file):
                    with open(skill_file) as f:
                        snap["skills_content"][name] = f.read()

        tools_dir = os.path.join(iter_dir, "tools")
        if os.path.exists(tools_dir):
            for name in os.listdir(tools_dir):
                tool_file = os.path.join(tools_dir, name, "SKILL.md")
                if os.path.exists(tool_file):
                    with open(tool_file) as f:
                        snap["tools_content"][name] = f.read()

        return metadata, snap

    def get_latest_checkpoint(self) -> tuple:
        """Find the latest checkpoint iteration.

        Returns:
            (iteration number, iter_dir path) or (None, None) if no checkpoints
        """
        if not os.path.exists(self.checkpoint_dir):
            return None, None

        iters = []
        for d in os.listdir(self.checkpoint_dir):
            if d.startswith("iter_"):
                try:
                    iters.append(int(d.split("_")[1]))
                except ValueError:
                    continue

        if not iters:
            return None, None

        latest = max(iters)
        return latest, os.path.join(self.checkpoint_dir, f"iter_{latest}")

    def evolve(self, n_iterations: int = 5, train_split=None, val_split=None,
               resume: bool = False):
        """Run the full evolution loop.

        Args:
            n_iterations: total iterations (iter 0 = baseline + iter 1..N-1 = evolution)
            train_split: pre-loaded train examples (for testing), or None to load from HF
            val_split: pre-loaded val examples (for testing), or None to load from HF
            resume: if True, resume from latest checkpoint
        """
        evolution_log = []
        start_iter = 0
        prev_val_acc = 0.0
        explore_margin = self.config["evolution"].get("explore_margin", 0.0)

        # Load data if not provided
        if train_split is None or val_split is None:
            from datasets import load_dataset
            dataset = load_dataset(self.config["evolution"]["train_dataset"])
            # Get the first (and likely only) split
            split_name = list(dataset.keys())[0]
            all_data = list(dataset[split_name])
            train_n = self.config["evolution"]["train_n"]
            train_split_raw = all_data[:train_n]
            val_split_raw = all_data[train_n:]
            train_split = self._prepare_examples(train_split_raw)
            val_split = self._prepare_examples(val_split_raw)

        # Augment train with A/B swaps for position invariance
        if self.config["evolution"].get("augment_swap", False):
            train_split = self._augment_with_swaps(train_split)
            logger.info(f"Augmented train split: {len(train_split)} examples (with A/B swaps)")

        # Resume from checkpoint if requested
        if resume:
            latest_iter, iter_dir = self.get_latest_checkpoint()
            if latest_iter is not None:
                metadata, snap = self._load_checkpoint(iter_dir)
                self.evolver.restore(snap)
                prev_val_acc = metadata.get("best_val_acc", metadata["val_acc"])
                start_iter = latest_iter + 1
                logger.info(f"Resumed from iter {latest_iter}, best_val_acc={prev_val_acc:.4f}")

                # Load existing log
                log_path = os.path.join(self.results_dir, "evolution_log.json")
                if os.path.exists(log_path):
                    with open(log_path) as f:
                        evolution_log = json.load(f)

        for iteration in range(start_iter, n_iterations):
            logger.info(f"\n{'='*60}")
            logger.info(f"Iteration {iteration}/{n_iterations-1}")
            logger.info(f"{'='*60}")

            iter_start = time.time()

            if iteration == 0:
                # Iter 0: baseline (empty library, pure Qwen reasoning)
                logger.info("Running baseline (empty library)...")
                train_results = self.run_iteration(train_split)
                train_acc = compute_kpair_accuracy(train_results, k=2)["accuracy"]

                val_results = self.run_iteration(val_split)
                val_acc = compute_kpair_accuracy(val_results, k=2)["accuracy"]
                prev_val_acc = val_acc

                snap = self.evolver.snapshot()
                self._checkpoint(iteration, snap, val_acc, train_acc)

                log_entry = {
                    "iteration": iteration,
                    "train_acc": train_acc,
                    "val_acc": val_acc,
                    "best_val_acc": val_acc,
                    "action": "baseline",
                    "skill_action": "skip",
                    "tool_action": "skip",
                    "val_acc_after_skills": None,
                    "val_acc_after_tools": None,
                    "n_skills": 0,
                    "n_tools": 0,
                    "duration_s": time.time() - iter_start,
                }
                evolution_log.append(log_entry)
                logger.info(f"Baseline: train_acc={train_acc:.4f}, val_acc={val_acc:.4f}")

            else:
                # Iter 1..N-1: evolution
                # 1. Run train split
                logger.info("Running train split...")
                train_results = self.run_iteration(train_split)
                train_acc = compute_kpair_accuracy(train_results, k=2)["accuracy"]
                logger.info(f"Train accuracy: {train_acc:.4f}")

                # 2. Chain analysis (all results, correct + incorrect)
                logger.info("Analyzing reasoning chains...")
                current_lib = self.library.get_all_summaries()
                signals = self.chain_analyzer.analyze(train_results, current_lib)
                skill_updates = signals.get("skill_updates", [])
                tool_updates = signals.get("tool_updates", [])
                logger.info(f"Signals: {len(skill_updates)} skill updates, "
                           f"{len(tool_updates)} tool updates")

                applied = {"skills_added": 0, "skills_updated": 0,
                           "tools_added": 0, "tools_updated": 0}
                old_val_acc = prev_val_acc
                skill_action = "skip"
                tool_action = "skip"
                val_acc_after_skills = None
                val_acc_after_tools = None

                # --- Phase A: Skills ---
                if skill_updates:
                    snap_before_skills = self.evolver.snapshot()
                    skill_signals = {"skill_updates": skill_updates,
                                     "tool_updates": [],
                                     "analysis_summary": signals.get("analysis_summary", "")}
                    logger.info("Phase A: Applying skill updates...")
                    skill_applied = self.evolver.apply_signals(skill_signals)
                    applied["skills_added"] = skill_applied["skills_added"]
                    applied["skills_updated"] = skill_applied["skills_updated"]

                    logger.info("Phase A: Running validation (skills)...")
                    val_results = self.run_iteration(val_split)
                    val_acc_after_skills = compute_kpair_accuracy(val_results, k=2)["accuracy"]

                    if val_acc_after_skills >= prev_val_acc - explore_margin:
                        skill_action = "keep"
                        prev_val_acc = max(prev_val_acc, val_acc_after_skills)
                        logger.info(f"Phase A KEEP: val_acc {old_val_acc:.4f} -> {val_acc_after_skills:.4f}")
                    else:
                        skill_action = "rollback"
                        self.evolver.restore(snap_before_skills)
                        logger.info(f"Phase A ROLLBACK: val_acc {val_acc_after_skills:.4f} < prev {prev_val_acc:.4f} - {explore_margin}")

                # --- Phase B: Tools ---
                if tool_updates:
                    snap_before_tools = self.evolver.snapshot()
                    tool_signals = {"skill_updates": [],
                                    "tool_updates": tool_updates,
                                    "analysis_summary": signals.get("analysis_summary", "")}
                    logger.info("Phase B: Applying tool updates...")
                    tool_applied = self.evolver.apply_signals(tool_signals)
                    applied["tools_added"] = tool_applied["tools_added"]
                    applied["tools_updated"] = tool_applied["tools_updated"]

                    logger.info("Phase B: Running validation (tools)...")
                    val_results = self.run_iteration(val_split)
                    val_acc_after_tools = compute_kpair_accuracy(val_results, k=2)["accuracy"]

                    if val_acc_after_tools >= prev_val_acc - explore_margin:
                        tool_action = "keep"
                        prev_val_acc = max(prev_val_acc, val_acc_after_tools)
                        logger.info(f"Phase B KEEP: val_acc -> {val_acc_after_tools:.4f}")
                    else:
                        tool_action = "rollback"
                        self.evolver.restore(snap_before_tools)
                        logger.info(f"Phase B ROLLBACK: val_acc {val_acc_after_tools:.4f} < prev {prev_val_acc:.4f} - {explore_margin}")

                # --- Phase C: Periodic Pruning ---
                prune_every_n = self.config["evolution"].get("prune_every_n", 0)
                pruned = None
                if prune_every_n > 0 and iteration > 0 and iteration % prune_every_n == 0:
                    logger.info(f"Phase C: Periodic pruning (every {prune_every_n} iters)...")
                    pruned = self._prune_library(val_split)
                    if pruned["pruned_skills"] or pruned["pruned_tools"]:
                        # Re-run val to get updated accuracy after pruning
                        val_results = self.run_iteration(val_split)
                        post_prune_acc = compute_kpair_accuracy(val_results, k=2)["accuracy"]
                        prev_val_acc = max(prev_val_acc, post_prune_acc)
                        logger.info(f"Phase C: post-prune val_acc={post_prune_acc:.4f}")

                # Backward compat: action = "keep" if either kept, "rollback" if both rolled back
                if skill_action == "keep" or tool_action == "keep":
                    action = "keep"
                elif skill_action == "rollback" or tool_action == "rollback":
                    action = "rollback"
                else:
                    action = "skip"

                # Checkpoint after both phases (save final state)
                final_snap = self.evolver.snapshot()
                self._checkpoint(iteration, final_snap, prev_val_acc, train_acc, signals,
                                 val_acc_after_skills=val_acc_after_skills,
                                 val_acc_after_tools=val_acc_after_tools)

                summaries = self.library.get_all_summaries()
                log_entry = {
                    "iteration": iteration,
                    "train_acc": train_acc,
                    "val_acc": val_acc_after_tools if val_acc_after_tools is not None else (
                        val_acc_after_skills if val_acc_after_skills is not None else prev_val_acc),
                    "prev_val_acc": old_val_acc,
                    "best_val_acc": prev_val_acc,
                    "action": action,
                    "skill_action": skill_action,
                    "tool_action": tool_action,
                    "val_acc_after_skills": val_acc_after_skills,
                    "val_acc_after_tools": val_acc_after_tools,
                    "applied": applied,
                    "analysis_summary": signals.get("analysis_summary", ""),
                    "n_skills": len(summaries["skills"]),
                    "n_tools": len(summaries["tools"]),
                    "pruned": pruned,
                    "duration_s": time.time() - iter_start,
                }
                evolution_log.append(log_entry)

            # Save evolution log after each iteration
            log_path = os.path.join(self.results_dir, "evolution_log.json")
            os.makedirs(self.results_dir, exist_ok=True)
            with open(log_path, 'w') as f:
                json.dump(evolution_log, f, indent=2)

        logger.info(f"\nEvolution complete. Final val_acc: {prev_val_acc:.4f}")
        return evolution_log
