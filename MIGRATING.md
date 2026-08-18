# Migrating to RewardHarness 0.3

RewardHarness 0.3 removes the deprecated `src.*` compatibility namespace that
was retained throughout the 0.2 release series. Runtime behavior, configuration
schema v2, Library files, CLI commands, and result formats remain unchanged.

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
   python -m pip install --upgrade "rewardharness>=0.3,<0.4"
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
