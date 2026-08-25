# Migrating to RewardHarness 0.4

RewardHarness 0.4 keeps the canonical `rewardharness.*` namespace introduced in
0.3 and modernizes configuration handling and interpreter support without
changing CLI commands, Library files, or result schemas.

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
