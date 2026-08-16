"""Command-line interface for RewardHarness workflows."""

from __future__ import annotations

import argparse
import base64
import json
import logging
from collections.abc import Sequence
from pathlib import Path

from rewardharness.benchmark import run_benchmark
from rewardharness.clients.endpoints import EndpointPool
from rewardharness.config import RewardHarnessConfig
from rewardharness.evaluation.engine import SUBAGENT_MODEL, SubAgent
from rewardharness.evaluation.router import Router
from rewardharness.evolution.pipeline import SelfEvolutionPipeline
from rewardharness.library import Library
from rewardharness.paths import PROJECT_ROOT, default_endpoints_path, default_library_path


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _encode(path: str) -> str:
    return base64.b64encode(_path(path).read_bytes()).decode()


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--library-dir")
    parser.add_argument("--results-dir")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rewardharness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("check", help="validate local credentials and endpoints")

    inspect_parser = subparsers.add_parser("inspect", help="inspect a Library registry")
    inspect_parser.add_argument("--library-dir", default=str(default_library_path()))

    validate_parser = subparsers.add_parser("validate-library", help="validate Library files")
    validate_parser.add_argument("--library-dir", default=str(default_library_path()))

    evolve_parser = subparsers.add_parser("evolve", help="run self-evolution")
    _add_common(evolve_parser)
    evolve_parser.add_argument("--resume", action="store_true")
    evolve_parser.add_argument("--max-iters", type=int)

    benchmark_parser = subparsers.add_parser("benchmark", help="run EditReward benchmark")
    _add_common(benchmark_parser)

    score_parser = subparsers.add_parser("score-pair", help="score two edited candidates")
    score_parser.add_argument("--source", required=True)
    score_parser.add_argument("--candidate-a", required=True)
    score_parser.add_argument("--candidate-b", required=True)
    score_parser.add_argument("--prompt", required=True)
    score_parser.add_argument("--library-dir", default=str(default_library_path()))
    score_parser.add_argument("--endpoints", default=str(default_endpoints_path()))
    score_parser.add_argument("--show-chain", action="store_true")
    return parser


def _load_config(path: str) -> RewardHarnessConfig:
    return RewardHarnessConfig.from_yaml(_path(path))


def _inspect(library_dir: str, validate: bool = False) -> int:
    library = Library(str(_path(library_dir)))
    if validate:
        for name in library.registry:
            library.get_full_content(name)
    print(json.dumps(library.get_all_summaries(), indent=2))
    return 0


def _evolve(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    pipeline = SelfEvolutionPipeline(config, args.library_dir, args.results_dir)
    iterations = args.max_iters or config.evolution.max_iterations
    log = pipeline.evolve(n_iterations=iterations, resume=args.resume)
    best = max(log, key=lambda entry: entry.get("val_acc", 0.0), default=None)
    if best:
        print(f"Best iteration: {best['iteration']} (val_acc={best['val_acc']:.4f})")
    return 0


def _benchmark(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    run_benchmark(config.to_legacy_dict(), args.library_dir, args.results_dir)
    return 0


def _score_pair(args: argparse.Namespace) -> int:
    library = Library(str(_path(args.library_dir)))
    context = Router(library).prepare_context(args.prompt)
    pool = EndpointPool(endpoints_file=str(_path(args.endpoints)))
    result = SubAgent(library, pool).evaluate(
        source_img=_encode(args.source),
        edited_A=_encode(args.candidate_a),
        edited_B=_encode(args.candidate_b),
        prompt=args.prompt,
        skill_context=context,
    )
    output = (
        result
        if args.show_chain
        else {key: value for key, value in result.items() if key != "chain"}
    )
    print(json.dumps({"model": SUBAGENT_MODEL, "result": output}, indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    args = build_parser().parse_args(argv)
    if args.command == "check":
        from rewardharness.diagnostics import main as diagnostics_main

        return diagnostics_main()
    if args.command == "inspect":
        return _inspect(args.library_dir)
    if args.command == "validate-library":
        return _inspect(args.library_dir, validate=True)
    if args.command == "evolve":
        return _evolve(args)
    if args.command == "benchmark":
        return _benchmark(args)
    if args.command == "score-pair":
        return _score_pair(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
