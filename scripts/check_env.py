#!/usr/bin/env python3
"""Preflight check before running RewardHarness pipelines.

Verifies that every environment dependency a real evolution / benchmark run
needs is in place — so you catch misconfiguration in 10 seconds instead of
after a 4-hour vLLM serve + evolution attempt.

Checks performed:
  1. Python version >= 3.10
  2. Core package imports (openai, google.genai, datasets, ...)
  3. Required env vars (GOOGLE_APPLICATION_CREDENTIALS, GEMINI_PROJECT)
  4. Credentials file readable + looks like a service-account JSON
  5. Optional: vLLM endpoints listed in configs/endpoints.txt are reachable

Exit code 0 if every required check passes, 1 otherwise. Optional checks
(vLLM endpoints) only warn — they don't fail the preflight.

Usage:
    python scripts/check_env.py
    make check
"""

import argparse
import importlib
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = RESET = ""

PASS, FAIL, WARN = f"{GREEN}PASS{RESET}", f"{RED}FAIL{RESET}", f"{YELLOW}WARN{RESET}"


def check_python_version() -> bool:
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 10)
    status = PASS if ok else FAIL
    print(f"  [{status}] Python {v.major}.{v.minor}.{v.micro} (need >= 3.10)")
    return ok


def check_imports() -> bool:
    required = ["openai", "google.genai", "datasets", "yaml", "PIL", "numpy"]
    missing = []
    for mod in required:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(f"  [{FAIL}] missing modules: {', '.join(missing)} — `pip install -r requirements.txt`")
        return False
    print(f"  [{PASS}] core imports ({', '.join(required)})")
    return True


def check_env_vars() -> bool:
    required = ["GOOGLE_APPLICATION_CREDENTIALS", "GEMINI_PROJECT"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"  [{FAIL}] env vars not set: {', '.join(missing)} — see .env.example")
        return False
    loc = os.environ.get("GEMINI_LOCATION", "global")
    print(f"  [{PASS}] GOOGLE_APPLICATION_CREDENTIALS, GEMINI_PROJECT (location={loc})")
    return True


def check_credentials_file() -> bool:
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not path:
        print(f"  [{FAIL}] GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    p = Path(path)
    if not p.is_file():
        print(f"  [{FAIL}] credentials file not found: {path}")
        return False
    try:
        data = json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"  [{FAIL}] credentials file is not valid JSON: {e}")
        return False
    sa_type = data.get("type", "")
    sa_email = data.get("client_email", "")
    if sa_type != "service_account":
        print(f'  [{FAIL}] credentials.type = {sa_type!r}, expected "service_account"')
        return False
    print(f"  [{PASS}] service-account key OK ({sa_email})")
    return True


def _probe_one(url: str, timeout: float) -> tuple[str, str]:
    """Return (url, status_line). status_line is human-readable; '' on success."""
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/models")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status == 200:
                return url, ""
            return url, f"HTTP {r.status}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return url, f"{type(e).__name__}: {e}"


def check_endpoints(endpoints_path: str, timeout: float = 3.0) -> bool:
    p = Path(endpoints_path)
    if not p.is_file():
        print(f"  [{WARN}] {endpoints_path} not found — skip endpoint probe")
        return True  # not required for preflight to pass
    urls = [
        line.strip()
        for line in p.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not urls:
        print(f"  [{WARN}] no endpoints listed in {endpoints_path}")
        return True
    # Probe in parallel so 16 unreachable endpoints take ~timeout, not 16*timeout.
    ok_count = 0
    with ThreadPoolExecutor(max_workers=min(16, len(urls))) as ex:
        for url, err in ex.map(lambda u: _probe_one(u, timeout), urls):
            if not err:
                ok_count += 1
                print(f"  [{PASS}] {url}")
            else:
                print(f"  [{WARN}] {url} -> {err}")
    if ok_count == 0:
        print(f"  [{WARN}] no endpoints reachable — bring one up with scripts/serve_vllm_multi.sh")
    else:
        print(f"  [{PASS}] {ok_count}/{len(urls)} endpoint(s) reachable")
    return True  # endpoint probe is informational only


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--endpoints",
        default="configs/endpoints.txt",
        help="Path to endpoints file (default: configs/endpoints.txt)",
    )
    args = parser.parse_args()

    print("RewardHarness preflight check\n")

    print("1. Python version")
    ok_py = check_python_version()
    print("\n2. Core package imports")
    ok_imports = check_imports()
    print("\n3. Required env vars")
    ok_env = check_env_vars()
    print("\n4. Service-account credentials")
    ok_creds = check_credentials_file() if ok_env else False
    print("\n5. vLLM endpoints (informational)")
    check_endpoints(args.endpoints)

    print()
    all_required = ok_py and ok_imports and ok_env and ok_creds
    if all_required:
        print(f"{GREEN}preflight: ALL REQUIRED CHECKS PASSED{RESET}")
        return 0
    print(f"{RED}preflight: ONE OR MORE REQUIRED CHECKS FAILED{RESET}")
    print("See TROUBLESHOOTING.md for fixes.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
