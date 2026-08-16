#!/usr/bin/env bash
# check_links.sh — Audit every markdown link in the repo's docs.
#
# Two checks per file:
#   1. Relative file paths exist on disk (always)
#   2. External URLs return HTTP 200 (only with --external; slow)
#
# Exit code 0 if all checks pass, 1 if any link is broken.
#
# Usage:
#   bash scripts/check_links.sh             # local file checks only (fast)
#   bash scripts/check_links.sh --external  # also curl every external URL

# shellcheck source=scripts/lib/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit

CHECK_EXTERNAL=0
[ "${1:-}" = "--external" ] && CHECK_EXTERNAL=1

DOCS=(
  README.md WALKTHROUGH.md TROUBLESHOOTING.md OUTPUTS.md
  CONTRIBUTING.md SECURITY.md CHANGELOG.md CLAUDE.md
  vanilla/README.md tests/README.md examples/README.md score-guidelines/README.md
)

broken=0

for doc in "${DOCS[@]}"; do
  [ -f "$doc" ] || continue
  base="$(dirname "$doc")"

  # 1. relative file links
  while IFS= read -r m; do
    [ -z "$m" ] && continue
    p=$(echo "$m" | sed -E 's/^\]\(//; s/\)$//; s/#.*//')
    [ -z "$p" ] && continue
    if [ ! -e "$base/$p" ] && [ ! -e "$p" ]; then
      echo "  BROKEN  $doc -> $p"
      broken=$((broken + 1))
    fi
  done < <(grep -oE '\]\([^):]+\)' "$doc" 2>/dev/null | grep -vE 'https?://|^]\(#|mailto:')

  # 2. external URLs (optional)
  if [ "$CHECK_EXTERNAL" = "1" ]; then
    while IFS= read -r url; do
      [ -z "$url" ] && continue
      # Skip URLs that are documentation examples, not real endpoints to validate:
      #   - http://localhost:* or http://127.0.0.1:* (sample curl commands)
      #   - example.com (placeholder in env-var defaults)
      if [[ "$url" =~ ^https?://(localhost|127\.0\.0\.1)([:/]|$) ]] || [[ "$url" =~ example\.com ]]; then
        continue
      fi
      # Drop -f so curl still emits %{http_code} on 4xx/5xx (otherwise we
      # get "429ERR" because || echo "ERR" appends to stdout). A real
      # connection failure leaves code empty; that's caught by the case below.
      code=$(curl -sS --max-time 8 -o /dev/null -w "%{http_code}" -L "$url" 2>/dev/null)
      [ -z "$code" ] && code="ERR"
      # 429 (rate-limit) means the host is up and refusing our HEAD; treat as reachable.
      # 301 also redirects; -L follows so we usually see the final 200/302.
      case "$code" in
        200|301|302|307|308|429) ;;
        *) echo "  HTTP $code  $doc -> $url"; broken=$((broken + 1)) ;;
      esac
    done < <(grep -oE 'https?://[^)>" ]+' "$doc" 2>/dev/null | sed -E 's/[.,;]$//' | sort -u)
  fi
done

if [ "$broken" = "0" ]; then
  echo "all checks passed."
  exit 0
else
  echo "$broken broken link(s) found."
  exit 1
fi
