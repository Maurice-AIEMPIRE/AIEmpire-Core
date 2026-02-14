#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

AUTO_COMMIT_ENABLED="${AUTO_COMMIT_ENABLED:-1}"
AUTO_COMMIT_PUSH="${AUTO_COMMIT_PUSH:-0}"
AUTO_COMMIT_MESSAGE_PREFIX="${AUTO_COMMIT_MESSAGE_PREFIX:-chore(auto): runtime sync}"
AUTO_COMMIT_PUSH_REMOTE="${AUTO_COMMIT_PUSH_REMOTE:-origin}"
AUTO_COMMIT_PUSH_BRANCH="${AUTO_COMMIT_PUSH_BRANCH:-}"

WORKFLOW="${1:-runtime}"
RUN_INDEX="${2:-}"
RUN_TOTAL="${3:-}"

if [ "$AUTO_COMMIT_ENABLED" != "1" ]; then
  echo "[auto-commit] disabled"
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[auto-commit] skipped: not a git repository"
  exit 0
fi

mkdir -p "$ROOT_DIR/00_SYSTEM"
LOCK_DIR="$ROOT_DIR/.git/auto_commit_runtime.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[auto-commit] skipped: another auto-commit is already running"
  exit 0
fi
cleanup() {
  rmdir "$LOCK_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if [ -f "$ROOT_DIR/.git/index.lock" ]; then
  if lsof "$ROOT_DIR/.git/index.lock" >/dev/null 2>&1; then
    echo "[auto-commit] skipped: git index.lock is currently in use"
    exit 0
  fi
  rm -f "$ROOT_DIR/.git/index.lock"
fi

if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "[auto-commit] no changes detected"
  exit 0
fi

TS_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
MSG="$AUTO_COMMIT_MESSAGE_PREFIX [$WORKFLOW]"
if [ -n "$RUN_INDEX" ] && [ -n "$RUN_TOTAL" ]; then
  MSG="$MSG run $RUN_INDEX/$RUN_TOTAL"
fi
MSG="$MSG $TS_UTC"

set +e
automation/scripts/commit_all.sh "$MSG"
COMMIT_RC=$?
set -e

if [ "$COMMIT_RC" -eq 1 ]; then
  echo "[auto-commit] nothing to commit"
  exit 0
fi
if [ "$COMMIT_RC" -ne 0 ]; then
  echo "[auto-commit] commit step failed (exit=$COMMIT_RC)"
  exit 0
fi

if [ "$AUTO_COMMIT_PUSH" = "1" ]; then
  BRANCH="$AUTO_COMMIT_PUSH_BRANCH"
  if [ -z "$BRANCH" ]; then
    BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  fi
  set +e
  git push "$AUTO_COMMIT_PUSH_REMOTE" "$BRANCH"
  PUSH_RC=$?
  set -e
  if [ "$PUSH_RC" -eq 0 ]; then
    echo "[auto-commit] pushed to $AUTO_COMMIT_PUSH_REMOTE/$BRANCH"
  else
    echo "[auto-commit] push failed (exit=$PUSH_RC) for $AUTO_COMMIT_PUSH_REMOTE/$BRANCH"
  fi
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto-commit executed ($WORKFLOW)" >> "$ROOT_DIR/00_SYSTEM/auto_commit.log"
