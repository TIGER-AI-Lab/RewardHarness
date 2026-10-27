# Migrating to RewardHarness 0.4

RewardHarness 0.4 keeps the canonical `rewardharness.*` namespace introduced in
0.3 and modernizes configuration handling and interpreter support without
changing CLI commands, Library files, or result schemas.

## Upcoming Python baseline (unreleased)

The source checkout now requires Python 3.11+ and Pillow 13.0.0+. Pillow 13
contains the fixes identified by the dependency audit and no longer supports
Python 3.10. This source change does not replace any already published wheel.

Create a new environment with Python 3.11 or newer instead of upgrading an
existing Python 3.10 environment in place:

```bash
python3.11 -m venv .venv311
.venv311/bin/python -m pip install -e .
.venv311/bin/python -m pip check
```

On Windows, use `py -3.11 -m venv .venv311` and
`.venv311\Scripts\python.exe` for the remaining commands. Model service and
optional GPU dependencies still have their own environment requirements.
Library and result schemas do not change as part of this baseline update.

## From 0.3 to 0.4

- `RewardHarnessConfig` is now retained throughout benchmark and evolution
  workflows instead of being converted back to a legacy dictionary.
- Use `RewardHarnessConfig.to_dict()` for schema-v2 serialization.
  `to_legacy_dict()` remains available as a compatibility alias.
- Evolution dataset loading now consumes exactly `train_n + val_n` rows and
  fails early if the configured split sizes cannot be satisfied.
- Python 3.13 is supported and continuously tested alongside 3.10–3.12.

No import changes are required when upgrading from 0.3.

## From 0.2 to 0.3

RewardHarness 0.3 removed the deprecated `src.*` compatibility namespace that
was retained throughout the 0.2 release series.

## Import replacements

| Removed import | Canonical replacement |
|---|---|
| `src.endpoint_pool` | `rewardharness.clients.endpoints` |
| `src.gemini_client` | `rewardharness.clients.gemini` |
| `src.library` | `rewardharness.library` |
| `src.router` | `rewardharness.evaluation.router` |
| `src.sub_agent` | `rewardharness.evaluation.engine` |
| `src.evaluator` | `rewardharness.evaluation.metrics` |
| `src.chain_analyzer` | `rewardharness.evolution.analyzer` |
| `src.evolver` | `rewardharness.evolution.evolver` |
| `src.pipeline` | `rewardharness.evolution.pipeline` |

Only the module path changes. Public symbol names such as `EndpointPool`,
`Library`, `Router`, `SubAgent`, `ChainAnalyzer`, `Evolver`, and
`SelfEvolutionPipeline` keep their v0.2 names and behavior.

## Upgrade checklist

1. Replace imports using the table above.
2. Upgrade and reject pre-release caching explicitly:

   ```bash
   python -m pip install --upgrade "rewardharness>=0.4,<0.5"
   ```

3. Confirm the installed package and configuration:

   ```bash
   rewardharness --version
   rewardharness validate-library
   rewardharness check --help
   ```

4. Search application code for remaining legacy imports:

   ```bash
   rg '(^|\s)(from|import) src(\.|\s|$)'
   ```

Projects that cannot migrate immediately should remain pinned to
`rewardharness>=0.2.2,<0.3`; the 0.3 wheel intentionally does not provide a
silent compatibility alias.

<!-- Release review: RewardHarness v0.4.1 (2026-08-26). -->
