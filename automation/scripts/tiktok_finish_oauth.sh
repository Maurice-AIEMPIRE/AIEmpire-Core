#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="$ROOT_DIR/ai-vault/empire.env"
CODE="${1:-}"
if [ -z "$CODE" ]; then
  echo "Usage: $0 <AUTH_CODE_FROM_CALLBACK_URL>" >&2
  exit 1
fi

set -a
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi
set +a

TMP_JSON="$(mktemp /tmp/tiktok_exchange_XXXXXX.json)"
trap 'rm -f "$TMP_JSON"' EXIT

python3 -m automation.tiktok exchange-code --code "$CODE" > "$TMP_JSON"

python3 - <<'PY' "$ENV_FILE" "$TMP_JSON"
import json, sys
from pathlib import Path

env_path = Path(sys.argv[1])
json_path = Path(sys.argv[2])

payload = json.loads(json_path.read_text('utf-8'))
# TikTok usually returns token fields under data
container = payload.get('data') if isinstance(payload, dict) and isinstance(payload.get('data'), dict) else payload
if not isinstance(container, dict):
    raise SystemExit('Unexpected TikTok token payload format')

access_token = str(container.get('access_token') or '').strip()
refresh_token = str(container.get('refresh_token') or '').strip()
expires_in = str(container.get('expires_in') or '').strip()
refresh_expires_in = str(container.get('refresh_expires_in') or '').strip()
open_id = str(container.get('open_id') or '').strip()

if not access_token:
    raise SystemExit('No access_token in TikTok response')

updates = {
    'TIKTOK_ACCESS_TOKEN': access_token,
    'TIKTOK_REFRESH_TOKEN': refresh_token,
    'TIKTOK_TOKEN_EXPIRES_IN': expires_in,
    'TIKTOK_REFRESH_EXPIRES_IN': refresh_expires_in,
    'TIKTOK_OPEN_ID': open_id,
}

text = env_path.read_text('utf-8', errors='ignore') if env_path.exists() else ''
lines = text.splitlines()
index = {}
for i, line in enumerate(lines):
    if '=' in line and not line.strip().startswith('#'):
        k = line.split('=', 1)[0].strip()
        index[k] = i

for key, value in updates.items():
    if not value:
        continue
    row = f'{key}={value}'
    if key in index:
        lines[index[key]] = row
    else:
        lines.append(row)

env_path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
print('Updated ai-vault/empire.env with TikTok OAuth tokens.')
print('TIKTOK_ACCESS_TOKEN=SET')
print('TIKTOK_REFRESH_TOKEN=' + ('SET' if refresh_token else 'MISSING'))
PY

echo
python3 -m automation.tiktok user-info || true
