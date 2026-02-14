#!/usr/bin/env bash
set -euo pipefail

PKGS=(
  edge-tts
  moviepy==1.0.3
  requests
  google-auth-oauthlib
  google-api-python-client
)

set +e
python3 -m pip install --upgrade "${PKGS[@]}"
RC=$?
set -e

if [ "$RC" -ne 0 ]; then
  echo "[deps] default install failed, retrying with --user --break-system-packages"
  python3 -m pip install --user --break-system-packages --upgrade "${PKGS[@]}"
fi

echo "Done. Installed faceless video + YouTube OAuth dependencies."
