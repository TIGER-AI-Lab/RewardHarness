# Changelog

All notable changes to RewardHarness are recorded here. Versions follow [SemVer](https://semver.org/). Dates are in ISO 8601 (UTC).

## [Unreleased]

Post-v0.1.2 polish, slated for v0.1.3:

### Added

- `scripts/check_links.sh` &mdash; audits every markdown link in the docs (relative paths always; external URLs with `--external`).
- `WALKTHROUGH.md` &mdash; 5-step Vertex AI service-account setup guide with direct GCP console deep-links.
- README release badge auto-updates from the latest GitHub tag.
- Per-author `affiliation` entries in the JSON-LD `ScholarlyArticle` block (21 author&ndash;org links).

### Changed

- `CLAUDE.md` rewritten with an explicit "for AI coding agents" preamble; dropped the internal-only `a-tool/edit-reward/` reference; tightened the no-coauthor rule to also forbid AI-attribution footers.
- README "Repository layout": `data/` row clarified (HuggingFace caches into `~/.cache/huggingface/`, not the repo's `data/` dir).
- Footer on the website lists both code mirrors (TIGER-AI-Lab / KlingAIResearch).

### Removed

- `vanilla/bench_wanqing.py` and hardcoded credentials from `vanilla/gemini_bench_*.py` (already shipped in v0.1.1's security patch; carrying the note here for completeness).
- Stale `data/checksums.txt` placeholder that no script ever populated.

### Fixed

- `scripts/run_evolution.py` now has the executable bit set, matching its siblings.
- `scripts/start_vllm_remote.sh` gained a header docstring explaining the SSH/Slurm invocation pattern.
- `scripts/reproduce.sh` step 4 now resets the `waited` counter per vLLM port (was a shared accumulator across all 16 ports, so the last few ports got near-zero timeout budget) and bumps per-port budget to 10 min for cold-start safety.
- `scripts/setup_env.sh` step labels harmonised &mdash; was `[1/3]`/`[2/3]`/`[3/3]`/`[4/5]`/`[5/5]`, now consistently `[N/5]`.
- `scripts/serve_vllm_multi.sh` &mdash; Bright Cluster Manager paths (`/cm/...`) are now overridable via `SLURM_PREFIX`, `CUDA_LIBS`, or skippable entirely with `RH_SKIP_ENV_PIN=1`. Previously broke `LD_LIBRARY_PATH` on vanilla Ubuntu/RHEL hosts.
- `scripts/download_data.sh` &mdash; dropped a dead checksum-generation step that wrote a `data/checksums.txt` no other script ever read. Replaced with a one-liner showing how to compare HuggingFace's built-in `_fingerprint` instead.

## [0.1.2] — 2026-05-16

### Added

- `examples/score_pair.py` &mdash; smallest-possible end-to-end script: Library + Router (Gemini) + SubAgent (vLLM) → 1&ndash;4 preference judgment for a single edit pair.
- `examples/sample_evolution_log.json` and `examples/sample_benchmark_results.json` &mdash; illustrative output files matching the paper's headline numbers; cross-linked from `OUTPUTS.md` so users can `jq`/diff their own runs.
- `.github/dependabot.yml` &mdash; weekly pip + monthly GitHub Actions security tracking.
- `MANIFEST.in` &mdash; ships `score-guidelines/*.md`, `examples/seed_library/`, and `configs/` in the sdist; closes a packaging hole where wheel installs were missing the runtime templates.
- `REWARDHARNESS_TEMPLATES_DIR` env-var escape hatch in `src/sub_agent.py` for unusual install layouts.
- `.editorconfig` for consistent contributor style.

### Changed

- README: new "Swapping in a different VLM as Sub-Agent" section explaining the two pluggability axes (OpenAI-compatible vs subclass); "What you can do with this code" 4-bullet hook near the top; Hardware-requirements table now lists per-workflow credentials.
- Website: new **Reasoning Trace** section showing a real `<think>/<tool>/<obs>/<answer>` chain; **"Why it works"** callout in Method section articulating the context-evolution thesis; brand SVG replaces the cross-platform-flaky 🦞 emoji in the title; Tutorial button replaces the dead `#` self-link.
- `make demo` and `make benchmark` default to `--library-dir examples/seed_library` for non-empty starting state.
- `make help` is now a credentials matrix showing what each target actually needs.

[0.1.2]: https://github.com/TIGER-AI-Lab/RewardHarness/releases/tag/v0.1.2

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
- Mermaid architecture diagram in README; per-folder READMEs (`tests/`, `examples/`, `vanilla/`, `score-guidelines/`).

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
- **Docs**: `README.md` with mermaid architecture diagram, Hardware-requirements table, full `default.yaml` reference, CI/coverage-style badges; `WALKTHROUGH.md` (9-step clone-to-first-judgment); `TROUBLESHOOTING.md`; per-folder READMEs for `tests/`, `examples/`, `vanilla/`, `score-guidelines/`; `CITATION.cff` so GitHub renders a "Cite this repository" widget.
- **License**: Apache-2.0.

### Performance (paper headline)

- **47.4%** average accuracy on EditReward-Bench + GenAI-Bench using the Gemini-2.0-Flash Sub-Agent (best K=2: 66.2 / K=3: 45.3 / GenAI: 64.4); **45.7%** with Qwen2.5-VL-7B (best K=3: 46.7 / GenAI: 67.5).
- Surpasses GPT-5 (42.1) by **+5.3** points using only **100 preference demonstrations** (0.05% of the EditReward training data).
- As a reward signal for GRPO fine-tuning of FLUX.2-klein-base-4B, raises ImgEdit-Bench from 3.32 → **3.52**, matching the much larger Flux.1 Kontext [dev].

[0.1.0]: https://github.com/TIGER-AI-Lab/RewardHarness/releases/tag/v0.1.0
