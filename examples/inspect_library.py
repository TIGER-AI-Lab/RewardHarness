"""Five-minute tour of the RewardHarness Library, without any API keys.

Run:
    python examples/inspect_library.py

This script:
  1. Creates a fresh empty Library in a temp directory.
  2. Adds one Skill (a declarative scoring rubric) and one Tool (a procedural
     in-context VLM spec).
  3. Prints the registry, the Skill markdown, and the Tool frontmatter.
  4. Demonstrates round-trip load: a second Library instance reading from the
     same path sees the same entries.

The data model exercised here is exactly what the Evolver mutates during a
real evolution run and what the Router selects from at inference time.
"""

import json
import os
import sys
import tempfile

# Make src/ importable when run from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.library import Library


def main():
    with tempfile.TemporaryDirectory() as base_dir:
        print(f"==> Initializing empty Library at {base_dir}")
        for sub in ("skills", "tools"):
            os.makedirs(os.path.join(base_dir, sub), exist_ok=True)
        with open(os.path.join(base_dir, "registry.json"), "w") as f:
            json.dump({}, f)

        lib = Library(base_dir)
        print(f"    Empty registry: {lib.registry}")

        # ----- Add a Skill -----
        print("\n==> Adding Skill: realism-and-artifact-penalties")
        lib.add_skill(
            name="realism-and-artifact-penalties",
            description="Penalize visual artifacts but allow conceptual unrealism when the prompt asks for it.",
            content_md=(
                "# Realism and Artifact Penalties\n\n"
                "1. Conceptual unrealism vs. visual artifacts: if the prompt asks for a surreal scene,\n"
                "   do NOT penalize for being unrealistic.\n"
                "2. Only penalize for processing artifacts: bad blending, visible seams, floating objects\n"
                "   with missing shadows, distorted textures.\n"
                "3. Between two images that follow the instruction, prefer the one with fewer artifacts.\n"
            ),
        )

        # ----- Add a Tool -----
        print("==> Adding Tool: text-and-ocr-analyzer")
        lib.add_tool(
            name="text-and-ocr-analyzer",
            description="OCR + verify spelling, placement, and clarity in edited images.",
            system_prompt=(
                "You are an expert OCR and text analysis AI. Extract all visible text from each image. "
                "Pay strict attention to spelling, typos, and placement."
            ),
            input_schema={"images": "list[base64_str]", "query": "str"},
            output_schema={"image_1_text": "str", "image_1_spelling_correct": "bool"},
            content_md=(
                "Use this tool whenever the prompt asks to add or modify text. "
                "It will read the exact spelling from the images so you can penalize typos or "
                "hallucinations."
            ),
        )

        # ----- Inspect -----
        print("\n==> Registry after adds:")
        print(json.dumps(lib.registry, indent=2))

        print("\n==> Skill file layout:")
        for root, _, files in os.walk(os.path.join(base_dir, "skills")):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), base_dir)
                print(f"    {rel}")

        print("\n==> Skill contents (realism-and-artifact-penalties):")
        skill = lib.get_skill("realism-and-artifact-penalties")
        print(f"    name        = {skill['name']}")
        print(f"    description = {skill['description']}")
        print("    content:")
        for line in skill["content"].splitlines():
            print(f"        {line}")

        # ----- Round-trip -----
        print("\n==> Round-trip: open a fresh Library instance against the same directory")
        lib2 = Library(base_dir)
        print(f"    Seen entries: {sorted(lib2.registry.keys())}")
        assert lib2.registry == lib.registry, "registry should match across instances"
        print("    OK — registry round-trips through disk.")

    print("\nDone. (Temp dir auto-cleaned.)")


if __name__ == "__main__":
    main()
