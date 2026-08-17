# Changelog

All notable changes to RewardHarness are recorded here. Versions follow [SemVer](https://semver.org/). Dates are in ISO 8601 (UTC).

## [Unreleased]

Future changes after the v0.2 release candidate.

## [0.2.0-rc1] — 2026-08-17

Large-scale architecture and release-hardening candidate. The supported API
now uses the `rewardharness` namespace, Library assets use schema v2, and the
deprecated `src` namespace remains as a compatibility layer for v0.2.

- Package metadata imports are now lazy, so version and release checks do not
  initialize model, dataset, or image-processing dependencies.
- Added canonical version/tag conversion, `rewardharness release-status`,
  cross-file release metadata validation, and post-publish PyPI/GitHub smoke
  verification.

### Added

- Active GitHub Actions CI now runs the test suite on Python 3.10&ndash;3.12,
  smoke-tests library inspection, and builds + validates wheel/sdist artifacts.
- `requirements-dev.txt`, `make install-dev`, and `make release-check` provide a
  reproducible maintainer path for testing and validating distributions.
- `scripts/check_links.sh` &mdash; audits every markdown link in the docs (relative paths always; external URLs with `--external`).
- `WALKTHROUGH.md` &mdash; 5-step Vertex AI service-account setup guide with direct GCP console deep-links; step 8 now shows the fast `python scripts/run_benchmark.py --config configs/default.yaml` paper-reproduction path against the shipped `rewardharness/resources/library/` (no evolution required first).
- README release badge auto-updates from the latest GitHub tag.
- Per-author `affiliation` entries in the JSON-LD `ScholarlyArticle` block (21 author&ndash;org links).
- `examples/score_pair.py --show-chain` flag to print the full `<think>/<tool>/<obs>/<answer>` reasoning trace.
- `REWARDHARNESS_SUBAGENT_MODEL` env var lets you swap in a non-Qwen OpenAI-compatible Sub-Agent without editing source. Honoured by **every** vLLM call site — `SubAgent._call_vllm`, `Library.call_tool`, `Evolver._validate_tool_prompt`, plus the server-side launchers `serve_vllm_multi.sh`, `_launch_all_vllm.sh`, `sbatch_vllm.sh`, and `start_vllm_remote.sh` — so VLM-swap setups are coherent end-to-end.
- `CLAUDE_API_BASE_URL` / `CLAUDE_API_KEY` env vars in `vanilla/bench_{claude,genaibench,imagenhub}.py`. Previously the URL was hardcoded to a dead internal proxy, so the Claude baselines were not reproducible without editing source.
- `.env.example` now lists every env var the code reads (13 new entries) &mdash; `REWARDHARNESS_SUBAGENT_MODEL`, the `serve_vllm_multi.sh` knobs (`NUM_GPUS`, `ENDPOINTS_PER_GPU`, `BASE_PORT`, `GPU_MEM`, `MAX_MODEL_LEN`, `VLLM_MODEL_PATH`), BCM cluster overrides (`RH_SKIP_ENV_PIN`, `SLURM_PREFIX`, `CUDA_LIBS`), Gemini gateway pair, Claude proxy pair. WALKTHROUGH step 4 (`cp .env.example .env`) is now a one-stop discovery mechanism.
- `scripts/run_evolution.py` end-of-run summary now surfaces the **best iteration** (highest `val_acc`) with a copy-paste-ready `--library-dir results/<run>/checkpoints/iter_N` hint, matching OUTPUTS.md's "pick the best post-hoc" guidance.

### Changed

- Test and release tooling is no longer installed as package runtime
  dependencies; published metadata now uses the SPDX `Apache-2.0` expression.
- `CLAUDE.md` rewritten with an explicit "for AI coding agents" preamble; dropped the internal-only `a-tool/edit-reward/` reference; tightened the no-coauthor rule to also forbid AI-attribution footers.
- `Makefile` &mdash; `make benchmark` defaults to the paper-evolved `rewardharness/resources/library/` (6 entries) instead of `examples/seed_library/` (3 entries). New users running `make benchmark` to verify paper headline numbers now see the actual paper accuracy instead of seed-library accuracy.
- README "Repository layout": `data/` row clarified (HuggingFace caches into `~/.cache/huggingface/`, not the repo's `data/` dir).
- README "Architecture": honest description of the evolution gate &mdash; replaces "kept only if held-out accuracy improves" with the actual `explore_margin` semantics (small dips permitted within tolerance).
- README "Key config" / `configs/default.yaml` &mdash; the `model:` block is now flagged INFORMATIONAL; no code reads those keys. Serving knobs are env vars consumed by `scripts/serve_vllm_multi.sh`.
- README "Updates" section now lists every released version (v0.1.0 / v0.1.1 / v0.1.2) with dates that match `CHANGELOG.md` + git tags. Previously off by one day on v0.1.0 and missing the v0.1.1 security release entirely.
- Footer on the website lists both code mirrors (TIGER-AI-Lab / KlingAIResearch).
- Website "Method" card now describes the actual phase A/B/C structure from `rewardharness/evolution/pipeline.py` instead of a fictitious "five stages" framing.
- Website figures now use `loading="lazy"` and `decoding="async"`, cutting first-paint bandwidth by ~820 KB for visitors who don't scroll past Abstract.
- Website "Try it yourself" callout now shows `--show-chain` (so the printed trace matches the section's headline example) and includes the no-image-needed fast path `python scripts/run_benchmark.py --config configs/default.yaml`.
- Website Table 2: Flux.1 Kontext [dev]'s 3.52 Overall is now marked second-best (matching the "tied at 3.52 with a smaller backbone" claim in the caption); previously RewardHarness's 3.52 was uniquely highlighted.
- Website mobile (≤735px): the dark-mode toggle stays visible (the previous CSS hid the whole `.nav-links` `<ul>`, taking the toggle with it).
- `vanilla/README.md` &mdash; backend/env-var table corrected: `gemini_bench_*.py` go through an OpenAI-compatible "Gemini gateway", not a direct Vertex AI client (their `--model` accepts Gemini or Claude ids — whatever your gateway supports).
- `rewardharness/resources/score_guidelines/README.md` rewritten: the templates ARE loaded by `rewardharness/evaluation/engine.py` at inference time (the old text claimed otherwise), and the internal scoring scale is 1-4 end-to-end (the old text claimed a 1-5 remap).
- WALKTHROUGH "Where things live" table &mdash; corrected the VLM-swap recipe: split into OpenAI-compatible (export env var, no source edit) and non-OpenAI (subclass) paths, matching what's actually in `rewardharness/evaluation/engine.py`.

### Removed

- `vanilla/bench_wanqing.py` and hardcoded credentials from `vanilla/gemini_bench_*.py` (already shipped in v0.1.1's security patch; carrying the note here for completeness).
- Stale `data/checksums.txt` placeholder that no script ever populated.

### Fixed

- The evolution pipeline's benchmark-data guard now raises an explicit error,
  so it remains active when Python runs with optimizations enabled.
- `scripts/run_evolution.py` now has the executable bit set, matching its siblings.
- `scripts/start_vllm_remote.sh` gained a header docstring explaining the SSH/Slurm invocation pattern, and now respects the same env-var conventions as `serve_vllm_multi.sh` (`VLLM_PYTHON`, `VLLM_MODEL_PATH`, `REWARDHARNESS_SUBAGENT_MODEL` via `--served-model-name`, `MAX_MODEL_LEN`).
- `scripts/reproduce.sh` step 4 now resets the `waited` counter per vLLM port (was a shared accumulator across all 16 ports, so the last few ports got near-zero timeout budget) and bumps per-port budget to 10 min for cold-start safety. **Also major fix:** step 4 reads `configs/endpoints.txt` (the same file the pipeline reads) instead of hardcoded ports 8000-8015, which mismatched `serve_vllm_multi.sh`'s 4-endpoint default and caused ~2 hours of timeout failure on default-config runs.
- `scripts/setup_env.sh` step labels harmonised &mdash; was `[1/3]`/`[2/3]`/`[3/3]`/`[4/5]`/`[5/5]`, now consistently `[N/5]`.
- `scripts/serve_vllm_multi.sh` &mdash; Bright Cluster Manager paths (`/cm/...`) are now overridable via `SLURM_PREFIX`, `CUDA_LIBS`, or skippable entirely with `RH_SKIP_ENV_PIN=1`. Previously broke `LD_LIBRARY_PATH` on vanilla Ubuntu/RHEL hosts.
- `scripts/download_data.sh` &mdash; dropped a dead checksum-generation step that wrote a `data/checksums.txt` no other script ever read. Replaced with a one-liner showing how to compare HuggingFace's built-in `_fingerprint` instead.
- `scripts/check_env.py` &mdash; vLLM endpoint probes now run in parallel (was sequential; with 16 endpoints all timing out, preflight took 48 s instead of ~3 s).
- `scripts/_launch_all_vllm.sh`, `scripts/sbatch_vllm.sh` &mdash; respect `NUM_GPUS` / `BASE_PORT` / `GPU_MEM` / `MAX_MODEL_LEN` / `VLLM_MODEL_PATH` env vars matching the public `serve_vllm_multi.sh`; previously hardcoded 4 GPUs and 0.85 GPU-mem. `sbatch_vllm.sh` also dropped two unsubstituted `/path/to/your/...` template paths in favour of a fail-fast `$RH_ROOT` requirement.
- `scripts/run_evolution_seed.sh` &mdash; generated YAML now uses `gemini:` (matching `configs/default.yaml`) instead of `claude:`, which would have `KeyError`'d at Router construction and also violated the no-Claude-API project rule.
- `scripts/run_all_benchmarks.sh` &mdash; summary table now shows `GenAI` and `average` columns (was only K=2/K=3/K=4), so the headline "which iter scored best on average" is visible at a glance. Inline-python invocation hardened (sys.argv instead of bash-substitution into source).
- `rewardharness/library/repository.py::call_tool` and `rewardharness/evolution/evolver.py::_validate_tool_prompt` &mdash; tool dispatches and Phase-B tool validation now read the same `SUBAGENT_MODEL` constant as `rewardharness/evaluation/engine.py`, so VLM-swap setups don't silently break inside `<tool>` blocks or new-tool acceptance.
- `examples/score_pair.py --show-chain` hint replaced a dead-end `result['chain']` instruction.
- `examples/inspect_library.py` and `examples/show_reasoning_format.py` verified clean against the current `rewardharness/resources/library` API (no signature drift).
- `examples/README.md` &mdash; corrected the "7-entry final library" claim to "6-entry (3 Skills + 3 Tools)", matching what's actually committed at `rewardharness/resources/library/`. Same correction landed on the website's Limitations card.
- `TROUBLESHOOTING.md` &mdash; corrected two doc/code drifts: the `/v1/models` health check shows `Qwen2.5-VL-7B-Instruct` (no `Qwen/` prefix), and the OOM mitigation now points at the actual `GPU_MEM` env var (default 0.85) instead of a non-existent `--gpu-memory-utilization` flag with the wrong default.
- `OUTPUTS.md` &mdash; documented the `_about` / `_library_dir` / `_orchestrator` / `_sub_agent` / `average` metadata fields the sample `benchmark_results.json` carries.
- `SECURITY.md` &mdash; "Supported versions" table now reflects v0.1.2 as latest (was still pointing at v0.1.1).
- `examples/show_reasoning_format.py` &mdash; corrected the tool-call limit (`MAX_TOOL_CALLS = 5` in `rewardharness/evaluation/engine.py`; was misdocumented as "default 3, bounded by config").
- `.github/ISSUE_TEMPLATE/bug_report.md` &mdash; the version-collection command `pip show A B C | head -3` was silently dropping the second and third packages; switched to `grep -E '^(Name|Version)'` which surfaces all three.
- `tests/` &mdash; added regression coverage for `REWARDHARNESS_SUBAGENT_MODEL` on all three vLLM call sites (`SubAgent`, `Library.call_tool`, `Evolver._validate_tool_prompt`); a future refactor that re-hardcodes the model id will now fail a test. Suite grew from 100 → 103 tests, still ~2 s.
- Website `script.js` dark-mode-toggle no longer wipes the inline SVG sun/moon icons with a Unicode entity on the first call &mdash; the CSS-based icon swap (already shipped) now works as designed.
- Website gallery click-to-enlarge actually works now. The lightbox handler in `script.js` was looking for a `.gallery-placeholder` child of `.gallery-item` that doesn't exist in the current Figure-4 markup (only an `<img>`), so clicks silently did nothing despite the subtitle's "click to enlarge" promise. Now falls back to cloning the `<img>` directly.
- `examples/score_pair.py` docstring now points at `REWARDHARNESS_SUBAGENT_MODEL` for non-Qwen swaps (was undiscoverable from the file new users read first).
- `OUTPUTS.md` + `examples/sample_benchmark_results.json` now honestly distinguish keys `scripts/run_benchmark.py` writes (`k2`/`k3`/`k4` with `n_pairs` + `pair_results`) from paper-headline-only fields (`genai_bench`, `average`) that require a separate GenAI-Bench pass. Includes a one-line `jq` merge recipe.
- `scripts/run_all_benchmarks.sh` summary table now renders `—` (em-dash) for missing GenAI/Avg keys instead of `0.0000`, since `run_benchmark.py` doesn't produce them by default — previously the table lied about scores it didn't have.
- `Makefile` `benchmark` target comment aligned with the iter-106 honesty pass: `make benchmark` actually reports K=2/3/4 on EditReward-Bench; the 45.7% / 47.4% headline averages also require a separate GenAI-Bench pass.
- `.env.example` &mdash; added the last 3 undocumented user-settable env vars (`RH_ROOT`, `SLURM_NODES_DIR`, `VLLM_PYTHON`). A grep diff against the codebase now finds no read-but-undocumented vars, so `cp .env.example .env` is a genuine single-point discovery mechanism.
- README "Datasets" table now lists `TIGER-Lab/GenAI-Bench` (`image_edition`, `test_v1`) alongside `EditReward-Data-100` and `EditReward-Bench`, flagged as paper-headline-only (not read by `run_benchmark.py`). Each row now also says which script consumes it.
- Website footer "Datasets:" line gets the same `TIGER-Lab/GenAI-Bench` link; the existing `TIGER-Lab/EditReward-Bench` blurb is now `(K=2/3/4 benchmark)` so the two benchmark datasets don't read identically.
- Website citation copy buttons: unified the BibTeX and Plain-text "Copy" handlers through a shared `initCopyButton(btnId, srcId)` helper in `script.js`. Previously the Plain-text button was an inline-onclick IIFE with no clipboard fallback and no error handling &mdash; it would show "Copied!" even when the underlying `navigator.clipboard.writeText` silently failed (denied permission, http-loaded page, older browser without `navigator.clipboard`). Now both use clipboard-API → `execCommand` fallback → `showCopied` only on real success.
- `scripts/check_links.sh --external` no longer reports false positives for documentation-example URLs (`http://localhost:*`, `127.0.0.1:*`, `example.com`) or rate-limited responses (HTTP 429 from e.g. `console.cloud.google.com`). Also fixed a latent bug where `curl -fsS … -w '%{http_code}'` + `|| echo "ERR"` was producing strings like `"429ERR"` instead of `"429"`, so the accept-list never matched. Now the script exits 0 on a clean repo against both relative-only and external runs.
- `examples/sample_evolution_log.json` + `OUTPUTS.md` now document **every** key `rewardharness/evolution/pipeline.py` writes to `evolution_log.json`: previously-missing `applied` (changes-counts dict), `analysis_summary` (string), `pruned` (mostly-empty list), and `duration_s` (wall-clock per iter). All 5 sample iters carry `duration_s` so the sample's total (~8.5 min) is a realistic expectation for `make demo` runtime.
- `WALKTHROUGH.md` step 8 + step 9 now reflect what `run_benchmark.py` / `make reproduce` actually produce (K=2/3/4 on EditReward-Bench), with explicit pointers to the GenAI-Bench merge recipe in `OUTPUTS.md` for users wanting to reach the paper's 47.4% / 45.7% headline averages. Step 9 renamed from "Full paper reproduction" → "End-to-end EditReward-Bench reproduction" for accuracy.
- Website `og:description` and `twitter:description` meta tags corrected: was `"47.4% on EditReward-Bench"`, now `"47.4% on EditReward-Bench + GenAI-Bench"` matching the visible TL;DR card and the paper definition.
- `website/site/sitemap.xml`'s `<lastmod>` bumped to today's date so search engines re-crawl after 50+ post-v0.1.2 website edits.
- README + WALKTHROUGH `make demo` timing claim corrected: was misleadingly "~30 min" (a holdover from when `demo` meant 5 iters), now "~3 min of pipeline work" matching the 1-iter Makefile target, with a note that vLLM cold-start dominates first-time runtime.
- `make help` text fixed: `make evolve` no longer claims "starts from empty library" (it actually loads `rewardharness/resources/library/` by default and evolves on top); `make reproduce` renamed from "End-to-end paper reproduction" → "End-to-end EditReward-Bench reproduction" matching iter 125's WALKTHROUGH change.
- `WALKTHROUGH.md` step 6 now shows the correct vLLM health-check output (`Qwen2.5-VL-7B-Instruct`, no `Qwen/` prefix &mdash; same fix iter 71 applied to TROUBLESHOOTING.md) and points at `.env.example` + README §Swapping Sub-Agent for users wanting to swap in a non-Qwen VLM.
- `TROUBLESHOOTING.md` &mdash; new entry covering the canonical VLM-swap failure mode: client `REWARDHARNESS_SUBAGENT_MODEL` mismatched with server `--served-model-name` returns `404 model not found`. Includes the matching client+server setup and a curl verification one-liner.
- `scripts/check_env.py` preflight now detects VLM-swap mismatches at the `/v1/models` probe step: parses `data[0].id` from each endpoint's response and warns if it differs from `REWARDHARNESS_SUBAGENT_MODEL`. Catches the iter-129 failure mode in ~3 seconds during `make check` instead of after a multi-hour evolution timeout. Imports the canonical `SUBAGENT_MODEL` constant from `src.sub_agent` so the script's expected baseline can't drift from the runtime's. Locked in by 4 new unit tests in `tests/test_check_env.py` (suite now 107 tests).
- Website "Try it yourself" callout in the Reasoning Trace section now says `run_benchmark.py` reproduces "the paper's EditReward-Bench K=2/3/4 numbers" (not "the paper's headline numbers") with a parenthetical pointer to OUTPUTS.md for the GenAI-Bench merge needed for the 47.4% average. Closes the last loose-promise instance of the iter-106 honesty pass on the live site.
- Test count claim updated from `~100 tests` → `~107 tests` in `tests/README.md`, `README.md` Repository-layout tree, and `CLAUDE.md` Commands block, matching the actual suite size after iters 79/97/131 added regression coverage. `tests/README.md` per-file table also gained a `test_check_env.py` row.
- README "Updates" section now cross-links `CHANGELOG.md [Unreleased]` with a one-line summary so visitors landing on the GitHub README can discover the post-v0.1.2 polish list in one click.
- README "Repository layout" tree filled out: previously omitted `examples/` entirely + `requirements-vllm.txt` + `.env.example` + all user-facing docs (`CHANGELOG.md`, `WALKTHROUGH.md`, `OUTPUTS.md`, `TROUBLESHOOTING.md`, `CONTRIBUTING.md`, `SECURITY.md`). All now visible with one-line descriptions of what's inside.
- `.gitignore` &mdash; dropped a stale `results_new/` line (dev-only artifact), and added `slurm-*.out` + `vllm-slurm-*.log` patterns so accidental Slurm-job log commits don't happen. **Caveat**: gitignore does **not** support inline `# comment`s on the pattern line; my first attempt buried the patterns inside what gitignore parsed as literal strings &mdash; verified-then-fixed in a same-iter follow-up commit.
- `OUTPUTS.md` &mdash; "Reading evolution_log" paragraph now mentions that `scripts/run_evolution.py` automatically surfaces the best iteration at end-of-run with a copy-paste-ready `--library-dir` hint (iter-105 UX win that was discoverable only by actually running the script). Also corrected the comparison key from `best_val_acc` (running max) to `val_acc` (per-iter, the actual comparison key).
- `examples/score_pair.py` now prints the resolved `SUBAGENT_MODEL` + endpoint count before invoking the SubAgent. A user with a typo'd `REWARDHARNESS_SUBAGENT_MODEL` or forgotten `export` sees the mismatch *before* the API call (catching the iter-129 "404 model not found" failure mode at config time instead of inside the evaluation).

## [0.1.2] — 2026-05-16

### Added

- `examples/score_pair.py` &mdash; smallest-possible end-to-end script: Library + Router (Gemini) + SubAgent (vLLM) → 1&ndash;4 preference judgment for a single edit pair.
- `examples/sample_evolution_log.json` and `examples/sample_benchmark_results.json` &mdash; illustrative output files matching the paper's headline numbers; cross-linked from `OUTPUTS.md` so users can `jq`/diff their own runs.
- `.github/dependabot.yml` &mdash; weekly pip + monthly GitHub Actions security tracking.
- `MANIFEST.in` &mdash; ships `rewardharness/resources/score_guidelines/*.md`, `examples/seed_library/`, and `configs/` in the sdist; closes a packaging hole where wheel installs were missing the runtime templates.
- `REWARDHARNESS_TEMPLATES_DIR` env-var escape hatch in `rewardharness/evaluation/engine.py` for unusual install layouts.
- `.editorconfig` for consistent contributor style.

### Changed

- README: new "Swapping in a different VLM as Sub-Agent" section explaining the two pluggability axes (OpenAI-compatible vs subclass); "What you can do with this code" 4-bullet hook near the top; Hardware-requirements table now lists per-workflow credentials.
- Website: new **Reasoning Trace** section showing a real `<think>/<tool>/<obs>/<answer>` chain; **"Why it works"** callout in Method section articulating the context-evolution thesis; brand SVG replaces the cross-platform-flaky 🦞 emoji in the title; Tutorial button replaces the dead `#` self-link.
- `make demo` and `make benchmark` default to `--library-dir examples/seed_library` for non-empty starting state.
- `make help` is now a credentials matrix showing what each target actually needs.

[0.1.2]: https://github.com/TIGER-AI-Lab/RewardHarness/releases/tag/v0.1.2
[0.2.0-rc1]: https://github.com/TIGER-AI-Lab/RewardHarness/releases/tag/v0.2.0-rc1

## [0.1.1] — 2026-05-16

### Security

- **Removed hardcoded internal API key** that was inadvertently shipped in `vanilla/bench_wanqing.py` and three `vanilla/gemini_bench_*.py` scripts in `v0.1.0`. The file `vanilla/bench_wanqing.py` is deleted; the three remaining scripts now read `GEMINI_GATEWAY_BASE_URL` and `GEMINI_GATEWAY_API_KEY` from the environment. See `SECURITY.md` for full disclosure timeline.

### Added

- `SECURITY.md` &mdash; responsible-disclosure policy and supported-version matrix.
- Substantial post-release polish across docs and examples:
  - `WALKTHROUGH.md` (9-step clone-to-first-judgment), `TROUBLESHOOTING.md`, `OUTPUTS.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.
  - `examples/seed_library/` (2 Skills + 1 Tool starter), `examples/show_reasoning_format.py`, `examples/score_pair.py`, `examples/sample_evolution_log.json`, `examples/sample_benchmark_results.json`.
  - `scripts/check_env.py` preflight; `make check` target.
  - `pyproject.toml` for editable install; `.env.example`; `requirements-vllm.txt` split out from the core deps.
  - GitHub issue templates + repo description/topics; CI workflow file prepared but not yet pushed (waiting on workflow scope).

### Changed

- `make demo` and `make benchmark` now default to `--library-dir examples/seed_library` so first-time users get non-trivial output without doing a 4&ndash;6 h evolution first.
- `src/__init__.py` exposes `__version__`.
- README adds a "Swapping in a different VLM as Sub-Agent" guide; Hardware-requirements table now lists credentials needed per workflow.
- Mermaid architecture diagram in README; per-folder READMEs (`tests/`, `examples/`, `vanilla/`, `rewardharness/resources/score_guidelines/`).

[0.1.1]: https://github.com/TIGER-AI-Lab/RewardHarness/releases/tag/v0.1.1

## [0.1.0] — 2026-05-15

Initial open-source release. Paper: [arXiv 2605.08703](https://arxiv.org/abs/2605.08703). Project page: [rewardharness.com](https://rewardharness.com).

### Added

- **Core framework** (`src/`): Orchestrator (Router + ChainAnalyzer + Evolver), frozen Sub-Agent reasoning loop, versioned Skills/Tools Library with snapshot/restore, Phase A/B/C self-evolution pipeline with gated rollback.
- **Reproduction scripts** (`scripts/`): `run_evolution.py`, `run_benchmark.py`, `reproduce.sh` (7-step end-to-end), multi-GPU vLLM launchers (`serve_vllm_multi.sh`, `sbatch_vllm.sh`), `check_env.py` preflight, `setup_env.sh`, `download_data.sh`.
- **Baseline benchmarks** (`vanilla/`): direct VLM scoring on EditReward-Bench / GenAI-Bench / ImagenHub with Claude- and Gemini-backed variants.
- **Test suite** (`tests/`, 100 tests, ~2 s): fully mocked Library / Router / SubAgent / Evolver / Pipeline / Evaluator tests with no GPU / network / API dependencies.
- **Examples** (`examples/`): `inspect_library.py` (Library data-model tour) and `show_reasoning_format.py` (annotated `<think>/<tool>/<obs>/<answer>` trace).
- **Build + packaging**: `Makefile` (install / check / test / demo / evolve / benchmark / reproduce / clean), `pyproject.toml` (editable install), split `requirements.txt` / `requirements-vllm.txt` so CPU-only workflows skip the heavy CUDA dependency, `.env.example`.
- **Docs**: `README.md` with mermaid architecture diagram, Hardware-requirements table, full `default.yaml` reference, CI/coverage-style badges; `WALKTHROUGH.md` (9-step clone-to-first-judgment); `TROUBLESHOOTING.md`; per-folder READMEs for `tests/`, `examples/`, `vanilla/`, `rewardharness/resources/score_guidelines/`; `CITATION.cff` so GitHub renders a "Cite this repository" widget.
- **License**: Apache-2.0.

### Performance (paper headline)

- **47.4%** average accuracy on EditReward-Bench + GenAI-Bench using the Gemini-2.0-Flash Sub-Agent (best K=2: 66.2 / K=3: 45.3 / GenAI: 64.4); **45.7%** with Qwen2.5-VL-7B (best K=3: 46.7 / GenAI: 67.5).
- Surpasses GPT-5 (42.1) by **+5.3** points using only **100 preference demonstrations** (0.05% of the EditReward training data).
- As a reward signal for GRPO fine-tuning of FLUX.2-klein-base-4B, raises ImgEdit-Bench from 3.32 → **3.52**, matching the much larger Flux.1 Kontext [dev].

[0.1.0]: https://github.com/TIGER-AI-Lab/RewardHarness/releases/tag/v0.1.0
