#!/usr/bin/env python3
"""
Google Drive Knowledge Sync - AIEmpire Cloud Backup.

Exportiert und synchronisiert ALLES Wissen auf Google Drive:
- Digital Memory (persistentes Gedaechtnis)
- n8n Knowledge Base (alle Agenten-Outputs)
- Gemini Mirror State (Sync, Evolution, Questions)
- Workflow Outputs (Compound Loop Ergebnisse)
- Gold Nuggets (Business Intelligence)
- System Configuration (alle Configs)

Zwei Methoden:
1. Google Drive API (mit Service Account oder OAuth)
2. gcloud/gsutil (Cloud Storage als Backup)

Usage:
    # Alles exportieren + auf Google Drive hochladen
    python scripts/cloud-sync/drive_sync.py --upload

    # Nur exportieren (lokales Backup)
    python scripts/cloud-sync/drive_sync.py --export

    # Von Google Drive herunterladen (Restore)
    python scripts/cloud-sync/drive_sync.py --download

    # Status anzeigen
    python scripts/cloud-sync/drive_sync.py --status

    # Daemon-Modus (alle 30 Min sync)
    python scripts/cloud-sync/drive_sync.py --daemon
"""

import os
import sys
import json
import shutil
import asyncio
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
EXPORT_DIR = PROJECT_ROOT / "cloud-export"
DRIVE_FOLDER = "AIEmpire-Knowledge"

# Alles was exportiert werden soll
KNOWLEDGE_SOURCES = {
    "digital_memory": {
        "source": PROJECT_ROOT / "gemini-mirror" / "state",
        "description": "Digital Memory - Persistentes Gedaechtnis",
        "files": ["memory.json", "memory_changelog.json",
                  "vision_questions.json", "vision_answers.json"],
    },
    "gemini_mirror": {
        "source": PROJECT_ROOT / "gemini-mirror" / "state",
        "description": "Gemini Mirror - Sync + Evolution State",
        "files": ["sync_log.json", "evolution_log.json",
                  "benchmark_log.json", "outbox_claude.json",
                  "outbox_gemini.json", "merged_state.json"],
    },
    "gemini_config": {
        "source": PROJECT_ROOT / "gemini-mirror",
        "description": "Gemini Mirror - Konfiguration",
        "files": ["config.yaml", "config.py"],
    },
    "n8n_knowledge": {
        "source": PROJECT_ROOT / "n8n-knowledge",
        "description": "n8n Knowledge Base - Komplettes Wissen",
        "files": ["n8n_complete_knowledge.json"],
    },
    "n8n_agents": {
        "source": PROJECT_ROOT / "n8n-knowledge" / "agents",
        "description": "n8n Agent Outputs - 10 Agent Ergebnisse",
        "files": ["*.json", "*.yaml", "*.py"],
        "glob": True,
    },
    "n8n_docker": {
        "source": PROJECT_ROOT / "n8n-knowledge",
        "description": "n8n Docker + API Bridge",
        "files": ["docker-compose.n8n.yaml", "n8n_api_bridge.py"],
    },
    "workflow_state": {
        "source": PROJECT_ROOT / "workflow-system" / "state",
        "description": "Workflow System - Aktueller State",
        "files": ["current_state.json", "cowork_state.json"],
    },
    "workflow_output": {
        "source": PROJECT_ROOT / "workflow-system" / "output",
        "description": "Workflow System - Alle Outputs",
        "glob": True,
        "files": ["*.json", "*.md"],
    },
    "gold_nuggets": {
        "source": PROJECT_ROOT / "gold-nuggets",
        "description": "Gold Nuggets - Business Intelligence",
        "glob": True,
        "files": ["*.md", "*.json", "INDEX.md"],
    },
    "n8n_workflows": {
        "source": PROJECT_ROOT / "n8n-workflows",
        "description": "n8n Workflows - Alle Workflow JSONs",
        "glob": True,
        "files": ["*.json"],
    },
    "products": {
        "source": PROJECT_ROOT / "products",
        "description": "Produkte - BMA Checklisten, etc.",
        "glob": True,
        "files": ["**/*.md"],
    },
    "empire_config": {
        "source": PROJECT_ROOT,
        "description": "Empire - Hauptkonfiguration",
        "files": ["CLAUDE.md", "requirements.txt", ".env.example"],
    },
    "docs": {
        "source": PROJECT_ROOT / "docs",
        "description": "Dokumentation - Alle Docs",
        "glob": True,
        "files": ["*.md"],
    },
}


class DriveSync:
    """Google Drive Knowledge Sync Engine."""

    def __init__(self):
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.stats = {
            "files_exported": 0,
            "files_uploaded": 0,
            "total_size_bytes": 0,
            "categories": {},
        }

    def export_all(self) -> dict:
        """Export all knowledge sources to local export directory."""
        print("\n[EXPORT] Collecting all knowledge...\n")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = EXPORT_DIR / timestamp
        export_path.mkdir(parents=True, exist_ok=True)

        for category, config in KNOWLEDGE_SOURCES.items():
            source = config["source"]
            desc = config["description"]
            cat_dir = export_path / category
            cat_dir.mkdir(parents=True, exist_ok=True)

            if not source.exists():
                print(f"  [{category:20s}] SKIP (source not found: {source})")
                continue

            file_count = 0
            cat_size = 0

            if config.get("glob"):
                # Glob patterns
                for pattern in config["files"]:
                    for f in source.glob(pattern):
                        if f.is_file():
                            dest = cat_dir / f.name
                            shutil.copy2(f, dest)
                            file_count += 1
                            cat_size += f.stat().st_size
            else:
                # Specific files
                for filename in config["files"]:
                    src = source / filename
                    if src.exists() and src.is_file():
                        shutil.copy2(src, cat_dir / filename)
                        file_count += 1
                        cat_size += src.stat().st_size

            self.stats["files_exported"] += file_count
            self.stats["total_size_bytes"] += cat_size
            self.stats["categories"][category] = {
                "files": file_count,
                "size_kb": round(cat_size / 1024, 1),
            }

            status = f"{file_count} files ({cat_size/1024:.1f} KB)"
            print(f"  [{category:20s}] {status}")

        # Write export manifest
        manifest = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "timestamp": timestamp,
            "project": "AIEmpire-Core",
            "owner": "Maurice Pfeifer",
            "stats": self.stats,
            "categories": {k: v["description"] for k, v in KNOWLEDGE_SOURCES.items()},
        }
        (export_path / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False)
        )

        # Create combined knowledge dump
        self._create_combined_dump(export_path)

        total_kb = self.stats["total_size_bytes"] / 1024
        print(f"\n  TOTAL: {self.stats['files_exported']} files ({total_kb:.1f} KB)")
        print(f"  Export: {export_path}")

        return {"path": str(export_path), "stats": self.stats}

    def _create_combined_dump(self, export_path: Path):
        """Create a single combined knowledge file for easy AI ingestion."""
        combined = {
            "meta": {
                "type": "AIEmpire Complete Knowledge Dump",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "purpose": "Complete knowledge export for AI learning and restoration",
            },
            "knowledge": {},
        }

        for category in KNOWLEDGE_SOURCES:
            cat_dir = export_path / category
            if not cat_dir.exists():
                continue

            combined["knowledge"][category] = {}
            for f in cat_dir.iterdir():
                if f.is_file() and f.suffix == ".json":
                    try:
                        combined["knowledge"][category][f.name] = json.loads(f.read_text())
                    except (json.JSONDecodeError, OSError):
                        combined["knowledge"][category][f.name] = {"error": "parse_failed"}
                elif f.is_file():
                    try:
                        content = f.read_text()
                        if len(content) < 50000:  # Skip huge files
                            combined["knowledge"][category][f.name] = content
                    except (UnicodeDecodeError, OSError):
                        pass

        dump_file = export_path / "COMPLETE_KNOWLEDGE_DUMP.json"
        dump_file.write_text(json.dumps(combined, indent=2, ensure_ascii=False))
        size = dump_file.stat().st_size / 1024
        print(f"\n  Combined dump: COMPLETE_KNOWLEDGE_DUMP.json ({size:.1f} KB)")

    def upload_to_drive(self, export_path: str = None) -> dict:
        """Upload export to Google Drive via gcloud/gdrive CLI."""

        if not export_path:
            # Find latest export
            exports = sorted(EXPORT_DIR.iterdir())
            if not exports:
                return {"error": "No exports found. Run --export first."}
            export_path = str(exports[-1])

        path = Path(export_path)
        if not path.exists():
            return {"error": f"Export path not found: {export_path}"}

        print(f"\n[UPLOAD] Uploading to Google Drive...")
        print(f"  Source: {path}")
        print(f"  Target: {DRIVE_FOLDER}/\n")

        # Method 1: Try rclone (best for Google Drive)
        if shutil.which("rclone"):
            return self._upload_rclone(path)

        # Method 2: Try gsutil (Google Cloud Storage → mountable as Drive)
        if shutil.which("gsutil") or shutil.which("gcloud"):
            return self._upload_gcs(path)

        # Method 3: Use Google Drive API directly via Python
        return self._upload_api(path)

    def _upload_rclone(self, path: Path) -> dict:
        """Upload via rclone (supports Google Drive natively)."""
        remote = "gdrive"  # Configure with: rclone config
        target = f"{remote}:{DRIVE_FOLDER}/{path.name}"

        try:
            result = subprocess.run(
                ["rclone", "copy", str(path), target, "--progress", "--transfers", "8"],
                capture_output=True, text=True, timeout=600,
            )

            if result.returncode == 0:
                print(f"  [rclone] Upload complete: {target}")
                return {"status": "uploaded", "method": "rclone", "target": target}
            else:
                print(f"  [rclone] Error: {result.stderr[:200]}")
                return {"status": "failed", "method": "rclone", "error": result.stderr[:200]}
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"status": "failed", "method": "rclone", "error": str(e)}

    def _upload_gcs(self, path: Path) -> dict:
        """Upload to Google Cloud Storage (accessible from Drive)."""
        bucket = os.environ.get("GCS_BUCKET", "ai-empire-knowledge")
        target = f"gs://{bucket}/{DRIVE_FOLDER}/{path.name}/"

        try:
            # Use gcloud storage cp (newer) or gsutil (older)
            cmd = ["gcloud", "storage", "cp", "--recursive", str(path), target]
            if not shutil.which("gcloud"):
                cmd = ["gsutil", "-m", "cp", "-r", str(path), target]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                print(f"  [gcs] Upload complete: {target}")
                return {"status": "uploaded", "method": "gcs", "target": target}
            else:
                err = result.stderr[:300]
                print(f"  [gcs] Error: {err}")
                # If bucket doesn't exist, try to create it
                if "not found" in err.lower() or "does not exist" in err.lower():
                    print(f"  [gcs] Creating bucket {bucket}...")
                    subprocess.run(
                        ["gcloud", "storage", "buckets", "create",
                         f"gs://{bucket}", "--location=europe-west1"],
                        capture_output=True, text=True, timeout=30,
                    )
                    # Retry upload
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                    if result.returncode == 0:
                        print(f"  [gcs] Upload complete (after bucket creation): {target}")
                        return {"status": "uploaded", "method": "gcs", "target": target}

                return {"status": "failed", "method": "gcs", "error": err}
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"status": "failed", "method": "gcs", "error": str(e)}

    def _upload_api(self, path: Path) -> dict:
        """Upload via Google Drive API (Python)."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except ImportError:
            print("  [api] Google API libraries not installed.")
            print("  Install: pip install google-api-python-client google-auth-oauthlib")
            print("\n  Alternatively install rclone:")
            print("    brew install rclone && rclone config  # choose Google Drive")
            print("\n  Or use gcloud:")
            print("    gcloud storage cp -r cloud-export/ gs://your-bucket/")
            return {
                "status": "no_upload_method",
                "message": "Install rclone, gcloud, or google-api-python-client",
                "export_path": str(path),
            }

        SCOPES = ["https://www.googleapis.com/auth/drive.file"]
        creds = None

        token_file = PROJECT_ROOT / "scripts" / "cloud-sync" / "token.json"
        creds_file = PROJECT_ROOT / "scripts" / "cloud-sync" / "credentials.json"

        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

        if not creds or not creds.valid:
            if not creds_file.exists():
                print("  [api] No credentials.json found.")
                print("  Download from: https://console.cloud.google.com/apis/credentials")
                print(f"  Save as: {creds_file}")
                return {"status": "no_credentials", "path": str(creds_file)}

            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)
            token_file.write_text(creds.to_json())

        service = build("drive", "v3", credentials=creds)

        # Create or find folder
        folder_id = self._get_or_create_drive_folder(service, DRIVE_FOLDER)

        # Upload files
        uploaded = 0
        for f in sorted(path.rglob("*")):
            if not f.is_file():
                continue

            rel_path = f.relative_to(path)
            mime = "application/json" if f.suffix == ".json" else "text/plain"

            media = MediaFileUpload(str(f), mimetype=mime)
            file_metadata = {
                "name": str(rel_path),
                "parents": [folder_id],
            }
            service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            uploaded += 1
            print(f"  Uploaded: {rel_path}")

        print(f"\n  [api] {uploaded} files uploaded to Google Drive: {DRIVE_FOLDER}/")
        return {"status": "uploaded", "method": "api", "files": uploaded}

    def _get_or_create_drive_folder(self, service, name: str) -> str:
        """Find or create a Google Drive folder."""
        results = service.files().list(
            q=f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
        ).execute()

        folders = results.get("files", [])
        if folders:
            return folders[0]["id"]

        folder_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=folder_metadata, fields="id").execute()
        return folder["id"]

    def download_from_drive(self) -> dict:
        """Download latest backup from Google Drive."""
        print("\n[DOWNLOAD] Not yet implemented - use rclone or gcloud:")
        print(f"  rclone copy gdrive:{DRIVE_FOLDER}/ cloud-export/restore/")
        print(f"  gcloud storage cp -r gs://ai-empire-knowledge/{DRIVE_FOLDER}/ cloud-export/restore/")
        return {"status": "manual", "instructions": "Use rclone or gcloud"}

    def show_status(self) -> dict:
        """Show sync status."""
        print("\n[DRIVE SYNC STATUS]\n")

        # Local exports
        if EXPORT_DIR.exists():
            exports = sorted(EXPORT_DIR.iterdir())
            print(f"  Local exports: {len(exports)}")
            for exp in exports[-3:]:
                manifest = exp / "MANIFEST.json"
                if manifest.exists():
                    m = json.loads(manifest.read_text())
                    files = m.get("stats", {}).get("files_exported", "?")
                    size = m.get("stats", {}).get("total_size_bytes", 0) / 1024
                    print(f"    {exp.name}: {files} files ({size:.1f} KB)")
                else:
                    print(f"    {exp.name}")
        else:
            print("  No local exports yet")

        # Upload tools
        print(f"\n  Upload methods available:")
        print(f"    rclone:  {'YES' if shutil.which('rclone') else 'NO (brew install rclone)'}")
        print(f"    gcloud:  {'YES' if shutil.which('gcloud') else 'NO (brew install google-cloud-sdk)'}")
        print(f"    gsutil:  {'YES' if shutil.which('gsutil') else 'NO'}")

        # Check google API libs
        try:
            import googleapiclient
            print(f"    API lib: YES")
        except ImportError:
            print(f"    API lib: NO (pip install google-api-python-client)")

        # Knowledge source status
        print(f"\n  Knowledge sources ({len(KNOWLEDGE_SOURCES)}):")
        for cat, config in KNOWLEDGE_SOURCES.items():
            exists = config["source"].exists()
            status = "READY" if exists else "MISSING"
            print(f"    {cat:20s} {status:7s} {config['description']}")

        return {"exports": len(list(EXPORT_DIR.iterdir())) if EXPORT_DIR.exists() else 0}


async def daemon_mode(interval: int = 1800):
    """Auto-sync every N seconds."""
    sync = DriveSync()
    print(f"\n[DAEMON] Auto-sync every {interval}s (Ctrl+C to stop)\n")

    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*50}")
        print(f"[SYNC CYCLE {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        result = sync.export_all()
        upload_result = sync.upload_to_drive(result["path"])

        print(f"  Upload: {upload_result.get('status', 'unknown')}")
        print(f"\n[NEXT] in {interval}s...")
        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Google Drive Knowledge Sync")
    parser.add_argument("--export", action="store_true", help="Export all knowledge locally")
    parser.add_argument("--upload", action="store_true", help="Export + upload to Google Drive")
    parser.add_argument("--download", action="store_true", help="Download from Google Drive")
    parser.add_argument("--status", action="store_true", help="Show sync status")
    parser.add_argument("--daemon", action="store_true", help="Auto-sync mode")
    parser.add_argument("--interval", type=int, default=1800, help="Daemon interval (seconds)")
    args = parser.parse_args()

    sync = DriveSync()

    if args.status:
        sync.show_status()
    elif args.export:
        sync.export_all()
    elif args.upload:
        result = sync.export_all()
        sync.upload_to_drive(result["path"])
    elif args.download:
        sync.download_from_drive()
    elif args.daemon:
        asyncio.run(daemon_mode(args.interval))
    else:
        sync.show_status()


if __name__ == "__main__":
    main()
