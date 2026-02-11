#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR" || exit 1

if [[ $# -ge 1 ]]; then
  MSG="$*"
else
  MSG="chore: workspace sync $(date +%Y-%m-%d_%H-%M-%S)"
fi

echo "[commit_all] Staging all changes..."
git add -A

# Safety filter: do not commit generated caches or local env secrets by default.
while IFS= read -r path; do
  if [[ "$path" == *"/__pycache__/"* ]] || [[ "$path" == *.pyc ]] || [[ "$path" == *.env ]] || [[ "$path" == "ai-vault/empire.env" ]]; then
    git restore --staged -- "$path" 2>/dev/null || true
  fi
done < <(git diff --cached --name-only)

if git diff --cached --quiet; then
  echo "[commit_all] Nothing to commit after safety filters."
  exit 1
fi

SECRET_RE='(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]+|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AIza[0-9A-Za-z\-_]{35})'
if git diff --cached | rg -n "$SECRET_RE" >/tmp/commit_all_secret_scan.txt 2>/dev/null; then
  echo "[commit_all] Potential secret detected in staged diff. Commit aborted."
  echo "[commit_all] Matches:"
  cat /tmp/commit_all_secret_scan.txt
  exit 3
fi
rm -f /tmp/commit_all_secret_scan.txt

echo "[commit_all] Commit message:"
echo "  $MSG"

git commit -m "$MSG"
echo "[commit_all] Done."
