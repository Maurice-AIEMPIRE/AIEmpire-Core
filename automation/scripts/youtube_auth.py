#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLIENT_SECRET = ROOT / "client_secret.json"
DEFAULT_ENV_FILE = ROOT / "ai-vault" / "empire.env"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _upsert_env(env_path: Path, updates: Dict[str, str]) -> None:
    lines = env_path.read_text("utf-8", errors="ignore").splitlines() if env_path.exists() else []
    index: Dict[str, int] = {}
    for i, line in enumerate(lines):
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            index[key] = i

    for key, value in updates.items():
        row = f"{key}={value}"
        if key in index:
            lines[index[key]] = row
        else:
            lines.append(row)

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run YouTube OAuth and print/store refresh token")
    parser.add_argument("--client-secret", default=str(DEFAULT_CLIENT_SECRET), help="Path to OAuth client_secret.json")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Where to store YOUTUBE_REFRESH_TOKEN")
    parser.add_argument("--no-write-env", action="store_true", help="Do not write tokens into env file")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open browser")
    args = parser.parse_args()

    client_secret_path = Path(args.client_secret).expanduser().resolve()
    env_path = Path(args.env_file).expanduser().resolve()

    if not client_secret_path.exists():
        raise SystemExit(f"Missing OAuth client file: {client_secret_path}")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except Exception as exc:
        raise SystemExit(
            "Missing dependency google-auth-oauthlib. Install with: "
            "python3 -m pip install google-auth-oauthlib google-api-python-client"
        ) from exc

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
    creds = flow.run_local_server(
        host="localhost",
        port=0,
        open_browser=not args.no_browser,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    payload = {
        "client_secret_path": str(client_secret_path),
        "scope": SCOPES,
        "token": bool(getattr(creds, "token", None)),
        "refresh_token": str(getattr(creds, "refresh_token", "") or ""),
        "token_uri": str(getattr(creds, "token_uri", "") or ""),
        "expiry": str(getattr(creds, "expiry", "") or ""),
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))

    refresh = payload["refresh_token"]
    if not refresh:
        print(
            "\nWARNING: No refresh_token returned. Remove previous app consent and run again with prompt=consent.\n"
            "Google Account -> Security -> Third-party access -> remove app, then rerun script."
        )
        return 0

    if not args.no_write_env:
        _upsert_env(
            env_path,
            {
                "YOUTUBE_REFRESH_TOKEN": refresh,
            },
        )
        print(f"\nUpdated {env_path} with YOUTUBE_REFRESH_TOKEN.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
