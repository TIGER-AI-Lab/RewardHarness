---
name: Bug report
about: Something broke. Include enough to reproduce.
title: "[bug] "
labels: bug
---

## Summary
A one-line description of what went wrong.

## Reproduction
```bash
# Exact command(s). Include `make check` output if relevant.
```

## Expected vs. actual
- Expected: …
- Actual: …

## Environment
- OS / GPU(s):
- Python: `python --version`
- `pip show vllm google-genai openai | head -3`
- Output of `make check` (or `python scripts/check_env.py`):

## Logs / stack trace
<details>
<summary>Click to expand</summary>

```
(paste here)
```
</details>

## Anything else
Relevant config diffs, hypotheses, prior issues you searched, etc.
