#!/usr/bin/env bash
# Shared runtime invariants for RewardHarness shell entry points.

set -Eeuo pipefail

RH_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RH_PYTHON="${VLLM_PYTHON:-python}"
readonly RH_PROJECT_ROOT RH_PYTHON

rh_log() {
  printf '[rewardharness] %s\n' "$*"
}

rh_require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'error: required command not found: %s\n' "$1" >&2
    return 127
  }
}

rh_on_error() {
  local exit_code=$?
  printf 'error: %s failed at line %s (exit %s)\n' "${BASH_SOURCE[1]}" "$1" "$exit_code" >&2
  return "$exit_code"
}

trap 'rh_on_error "$LINENO"' ERR
