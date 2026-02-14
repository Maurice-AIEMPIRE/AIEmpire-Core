#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
ATLAS_CLI="${ATLAS_CLI:-$CODEX_HOME/skills/atlas/scripts/atlas_cli.py}"
OUT_DIR="${ATLAS_SNAPSHOT_DIR:-$ROOT_DIR/external/imports/atlas_history}"
HISTORY_LIMIT="${ATLAS_HISTORY_LIMIT:-200}"
RUN_TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUT_DIR"

if [ ! -f "$ATLAS_CLI" ]; then
  echo "[atlas-snapshot] atlas_cli not found at $ATLAS_CLI"
  exit 0
fi

APP_NAME="$(uv run --python 3.12 python "$ATLAS_CLI" app-name 2>/dev/null || true)"
if [ -z "$APP_NAME" ]; then
  echo "[atlas-snapshot] Atlas app not available"
  exit 0
fi

TMP_TABS="$(mktemp)"
TMP_HISTORY="$(mktemp)"
trap 'rm -f "$TMP_TABS" "$TMP_HISTORY"' EXIT

if ! uv run --python 3.12 python "$ATLAS_CLI" tabs --json > "$TMP_TABS" 2>/dev/null; then
  echo "[]" > "$TMP_TABS"
fi
if ! uv run --python 3.12 python "$ATLAS_CLI" history --today --limit "$HISTORY_LIMIT" --json > "$TMP_HISTORY" 2>/dev/null; then
  echo "[]" > "$TMP_HISTORY"
fi

OUT_FILE="$OUT_DIR/${RUN_TS}.json"

python3 - <<'PY' "$TMP_TABS" "$TMP_HISTORY" "$OUT_FILE" "$APP_NAME"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

tabs_path = Path(sys.argv[1])
history_path = Path(sys.argv[2])
out_path = Path(sys.argv[3])
app_name = sys.argv[4]

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

payload = {
    "captured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "app_name": app_name,
    "tabs": load_json(tabs_path),
    "history_today": load_json(history_path),
}
out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
print(str(out_path))
PY

echo "[atlas-snapshot] wrote $OUT_FILE"
