#!/usr/bin/env python3
"""Run RewardHarness self-evolution pipeline.

Usage:
    python scripts/run_evolution.py --config configs/default.yaml
    python scripts/run_evolution.py --config configs/default.yaml --resume
    python scripts/run_evolution.py --config configs/default.yaml --max-iters 10
"""

import argparse
import logging
import os
import sys

import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import SelfEvolutionPipeline


def main():
    parser = argparse.ArgumentParser(description="Run RewardHarness self-evolution pipeline")
    parser.add_argument("--config", default="configs/default.yaml", help="Config file path")
    parser.add_argument("--resume", action="store_true", help="Resume from latest checkpoint")
    parser.add_argument("--max-iters", type=int, default=None, help="Override max iterations")
    parser.add_argument("--library-dir", default=None, help="Path to library directory")
    parser.add_argument("--results-dir", default=None, help="Path to results directory")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("evolution")

    # Load config
    config_path = os.path.join(PROJECT_ROOT, args.config) if not os.path.isabs(args.config) else args.config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    n_iterations = args.max_iters or config["evolution"].get("max_iterations", 5)

    logger.info(f"Config: {config_path}")
    logger.info(f"Iterations: {n_iterations}")
    logger.info(f"Resume: {args.resume}")
    logger.info(f"Train dataset: {config['evolution']['train_dataset']}")

    # Run pipeline
    pipeline = SelfEvolutionPipeline(config, library_dir=args.library_dir, results_dir=args.results_dir)
    evolution_log = pipeline.evolve(
        n_iterations=n_iterations,
        resume=args.resume
    )

    # Print summary
    print("\n" + "=" * 60)
    print("Evolution Summary")
    print("=" * 60)
    for entry in evolution_log:
        i = entry["iteration"]
        action = entry.get("action", "")
        val_acc = entry.get("val_acc", 0)
        train_acc = entry.get("train_acc", 0)
        n_skills = entry.get("n_skills", 0)
        n_tools = entry.get("n_tools", 0)
        print(f"  Iter {i}: train={train_acc:.4f}  val={val_acc:.4f}  "
              f"action={action}  skills={n_skills}  tools={n_tools}")
    print("=" * 60)

    results_dir = args.results_dir or os.path.join(PROJECT_ROOT, "results")
    results_path = os.path.join(results_dir, "evolution_log.json")
    print(f"\nFull log: {results_path}")


if __name__ == "__main__":
    main()
