# Examples

Standalone scripts that you can run **without GPUs, vLLM, or API keys** to understand the RewardHarness internals before launching a full evolution.

| Script | What it shows |
|---|---|
| [`inspect_library.py`](inspect_library.py) | Five-minute tour of the Library data model: adding a Skill, adding a Tool, printing the registry, and round-tripping through disk. No external calls. |

Run from the repo root:

```bash
python examples/inspect_library.py
```

Expected output: a few "==>" sections showing the registry contents, the skill markdown body, and an assertion that two Library instances opened against the same path see identical contents.

If you want to see the Library in action against a real Sub-Agent, run `make demo` instead (1-iteration evolution; requires Gemini + a single vLLM endpoint).
