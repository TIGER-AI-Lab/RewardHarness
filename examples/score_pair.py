"""Score a single edit pair end-to-end with RewardHarness.

Demonstrates the full inference path:
    Library  →  Router (Gemini, selects relevant skills/tools)
                  ↓
            skill_context
                  ↓
    SubAgent (vLLM, Qwen2.5-VL-7B)  →  scores + preference

Run:
    python examples/score_pair.py \\
        --source path/to/source.png \\
        --candidate-a path/to/A.png \\
        --candidate-b path/to/B.png \\
        --prompt "Make the computer have a futuristic design" \\
        --library-dir examples/seed_library

Required env vars (see .env.example):
    GOOGLE_APPLICATION_CREDENTIALS, GEMINI_PROJECT
    plus a vLLM endpoint listed in configs/endpoints.txt (Qwen2.5-VL-7B-Instruct)

Returns the same dict shape `scripts/run_benchmark.py` consumes:
    {
      "preference": "A" | "B" | "tie",
      "score_A_instruction": int,
      "score_A_quality":     int,
      "score_B_instruction": int,
      "score_B_quality":     int,
      "reasoning":           str,
      ... (plus chain trace)
    }
"""

import argparse
import base64
import json
import os
import sys

# Import from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.endpoint_pool import EndpointPool
from src.library import Library
from src.router import Router
from src.sub_agent import SubAgent


def b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--source", required=True, help="path to source image")
    p.add_argument("--candidate-a", required=True, help="path to candidate A")
    p.add_argument("--candidate-b", required=True, help="path to candidate B")
    p.add_argument("--prompt", required=True, help="editing instruction")
    p.add_argument("--library-dir", default="examples/seed_library",
                   help="path to evolved Library (default: examples/seed_library)")
    p.add_argument("--endpoints", default="configs/endpoints.txt",
                   help="path to vLLM endpoints file")
    p.add_argument("--show-chain", action="store_true",
                   help="also print the full <think>/<tool>/<obs>/<answer> reasoning chain")
    args = p.parse_args()

    print(f"==> Library: {args.library_dir}")
    lib = Library(args.library_dir)
    print(f"    {len(lib.registry)} entries: {sorted(lib.registry.keys())}")

    print(f"\n==> Router (Gemini) selects relevant skills/tools for the prompt")
    router = Router(lib)
    skill_context = router.prepare_context(args.prompt)
    print(f"    context bytes: {len(skill_context)}")

    print(f"\n==> SubAgent (vLLM) scores the pair")
    pool = EndpointPool(endpoints_file=args.endpoints)
    agent = SubAgent(lib, pool)
    result = agent.evaluate(
        source_img=b64(args.source),
        edited_A=b64(args.candidate_a),
        edited_B=b64(args.candidate_b),
        prompt=args.prompt,
        skill_context=skill_context,
    )

    print("\n==> Result")
    print(json.dumps(
        {k: v for k, v in result.items() if k != "chain"},
        indent=2,
    ))
    if "chain" in result:
        if args.show_chain:
            print("\n==> Reasoning chain")
            print(result["chain"])
        else:
            print("\n(reasoning chain omitted — re-run with --show-chain to print it)")


if __name__ == "__main__":
    main()
