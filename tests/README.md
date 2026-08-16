# Tests

Fully mocked end-to-end test suite (**138 tests**, runs in a few seconds) — no GPU,
no network, no API keys, and no real Gemini calls. Install development tooling
from `requirements-dev.txt` before running the complete quality gate.

```bash
# all tests
python -m pytest tests/ -v
# or
make test
```

| File | Scope |
|---|---|
| `conftest.py` | Shared pytest fixtures (e.g. `tmp_library`, mock VLM/Gemini clients). |
| `test_library.py` | Unit tests for the `Library` class — `add_skill`, `add_tool`, `get_*`, `update_*`, registry persistence. |
| `test_library_integration.py` | End-to-end Library lifecycle: snapshot/restore, registry consistency across multiple `Library` instances on the same disk. |
| `test_router.py` | `Router.prepare_context` — Gemini-driven Skill/Tool selection, empty-library short-circuit, malformed JSON recovery. |
| `test_sub_agent.py` | `SubAgent` reasoning loop — `<think>/<tool>/<obs>/<answer>` parsing, tool-call limit enforcement, fallback on no-answer. |
| `test_evaluator.py` | `evaluate_prediction` + K=2/3/4 group-accuracy computation. |
| `test_chain_evolver.py` | Full evolution micro-flow: failure examples → ChainAnalyzer → improvement signals → Evolver → SKILL.md on disk. |
| `test_pipeline.py` | `SelfEvolutionPipeline.evolve` over 2 iterations — separate skill/tool rollback, `>= prev - margin` keep condition, checkpoint write, val-acc regression triggers rollback. |
| `test_check_env.py` | `scripts/check_env.py::_probe_one` — `/v1/models` body parsing for the VLM-swap mismatch detection added in iter 130. |
| `test_public_api.py` | Typed v0.2 API, schema v2, compatibility imports, config validation, and path safety. |

Everything that touches an external service (Gemini, vLLM, Hugging Face) is mocked with `unittest.mock`. If a test ever makes a real network call, it's a regression — please open an issue.

## Running a single test

```bash
python -m pytest tests/test_pipeline.py::TestPipelineEvolution::test_two_iteration_run -v
```

## Adding tests

Mock the external boundary at the highest layer that's still meaningful:

- Need a Gemini response? Inject a completion callable or patch the relevant
  `rewardharness` client boundary.
- Need a vLLM completion? Patch `rewardharness.evaluation.engine.OpenAI`.

The fixtures in `conftest.py` already cover the common cases.
