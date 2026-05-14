# Examples

Standalone scripts that you can run **without GPUs, vLLM, or API keys** to understand the RewardHarness internals before launching a full evolution.

| Script | What it shows |
|---|---|
| [`inspect_library.py`](inspect_library.py) | Five-minute tour of the Library data model: adding a Skill, adding a Tool, printing the registry, and round-tripping through disk. Requires `openai` + `pyyaml`. |
| [`show_reasoning_format.py`](show_reasoning_format.py) | Prints a representative `<think>/<tool>/<obs>/<answer>` chain so you know what to expect when running the real Sub-Agent. Pure stdlib. |

Run from the repo root:

```bash
python examples/inspect_library.py
python examples/show_reasoning_format.py
```

`inspect_library.py` prints a few "==>" sections (registry contents, skill markdown, round-trip assertion). `show_reasoning_format.py` prints one annotated preference judgment with the tag legend and the pipeline's parsing rules.

If you want to see the Library in action against a real Sub-Agent, run `make demo` instead (1-iteration evolution; requires Gemini + a single vLLM endpoint).
