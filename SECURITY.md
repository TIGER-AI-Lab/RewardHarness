# Security policy

## Reporting a vulnerability

If you find a security issue (leaked credentials in code or commit history, command injection, etc.), **please do NOT open a public GitHub issue**.

Instead, email the maintainers at **<reacher.z@pm.me>** with:

- A short description of the issue
- Reproduction steps or proof-of-concept (commit SHA, file path, exploit input)
- Whether the issue is currently public anywhere
- Your suggested fix, if any

We aim to acknowledge reports within **5 business days** and ship a patch (or a documented mitigation) within **14 business days**.

## Supported versions

Only the current `main` branch and the most recent tagged release receive security fixes. We will not backport fixes to older tags.

| Version | Supported |
|---|---|
| `main` | ✅ |
| `v0.1.1` (latest) | ✅ |
| earlier | ❌ |

## Disclosure history

| Date | Issue | Fixed in |
|---|---|---|
| 2026-05-16 | A hardcoded internal Gemini-gateway API key was inadvertently shipped in `vanilla/bench_wanqing.py` and three `vanilla/gemini_bench_*.py` files in the initial `v0.1.0` release. The key was rotated upstream; current `vanilla/gemini_bench_*.py` reads credentials from `GEMINI_GATEWAY_API_KEY` instead. The leaked value remains in git history before commit `6b61e3d` &mdash; treat any token captured during that ~24 h window as compromised. | `v0.1.1` (`6b61e3d`) |

## Hardening notes

- `.gitignore` excludes every `.env*` except `.env.example`. Don't commit real `.env` files.
- The test suite is fully mocked and **must never make real network calls**. If a test reaches out, file a bug &mdash; it's a security smell.
- `scripts/check_env.py` validates that credentials look well-formed but never logs them.
- Service-account JSON files belong outside the repo tree. Reference them via `GOOGLE_APPLICATION_CREDENTIALS` only.
