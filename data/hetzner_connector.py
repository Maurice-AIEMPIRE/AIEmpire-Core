"""
Hetzner Storage Connector
==========================
Connects to Hetzner Storage Box or Hetzner Server via SFTP/SSH
to sync legal documents into the local data/inbox/ pipeline.

Supports:
  - Hetzner Storage Box (SFTP)
  - Hetzner Dedicated/Cloud Server (SSH + SFTP)
  - Incremental sync (only new/changed files)
  - File integrity verification (SHA256)

Privacy: All synced files stay LOCAL (P3). No cloud processing.

Usage:
    from data.hetzner_connector import HetznerConnector

    connector = HetznerConnector()
    new_files = await connector.sync_documents()
    print(f"Synced {len(new_files)} new documents")
"""

import asyncio
import hashlib
import json
import os
import stat
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Use config system (never os.getenv directly per CLAUDE.md)
try:
    from config.env_config import get_api_key
except ImportError:
    # Fallback for standalone usage
    def get_api_key(name: str) -> str:
        return os.getenv(name, "")


# ── Project paths ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_INBOX = PROJECT_ROOT / "data" / "inbox"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
SYNC_STATE_FILE = PROJECT_ROOT / "data" / ".hetzner_sync_state.json"

# ── Supported legal document extensions ───────────────────────────────
LEGAL_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls",
    ".txt", ".eml", ".msg", ".rtf", ".odt",
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp",  # Scans/Screenshots
    ".csv", ".json",
}


@dataclass
class HetznerConfig:
    """Configuration for Hetzner connection."""
    host: str = ""
    port: int = 22
    username: str = ""
    password: str = ""
    ssh_key_path: str = ""
    remote_base_path: str = "/legal"
    # Subdirectories on Hetzner to scan
    remote_dirs: list[str] = field(default_factory=lambda: [
        "/legal",
        "/dokumente",
        "/rechtsstreit",
        "/vertraege",
        "/korrespondenz",
    ])
    # Max file size to sync (100MB default)
    max_file_size_mb: int = 100

    @classmethod
    def from_env(cls) -> "HetznerConfig":
        """Load config from environment variables."""
        return cls(
            host=get_api_key("HETZNER_HOST"),
            port=int(get_api_key("HETZNER_PORT") or "22"),
            username=get_api_key("HETZNER_USER"),
            password=get_api_key("HETZNER_PASSWORD"),
            ssh_key_path=get_api_key("HETZNER_SSH_KEY_PATH"),
            remote_base_path=get_api_key("HETZNER_REMOTE_PATH") or "/legal",
        )


@dataclass
class SyncedFile:
    """Metadata for a synced file."""
    remote_path: str
    local_path: str
    filename: str
    size_bytes: int
    sha256: str
    synced_at: str
    file_type: str
    modified_at: str = ""


class HetznerConnector:
    """
    Connects to Hetzner server/storage box and syncs legal documents.

    Implements incremental sync: tracks what's been downloaded and only
    fetches new or modified files.
    """

    def __init__(self, config: Optional[HetznerConfig] = None):
        self.config = config or HetznerConfig.from_env()
        self._sftp = None
        self._transport = None
        self._sync_state: dict = {}
        self._load_sync_state()

    def _load_sync_state(self):
        """Load previous sync state to enable incremental sync."""
        if SYNC_STATE_FILE.exists():
            try:
                with open(SYNC_STATE_FILE, "r") as f:
                    self._sync_state = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._sync_state = {"files": {}, "last_sync": None}
        else:
            self._sync_state = {"files": {}, "last_sync": None}

    def _save_sync_state(self):
        """Save sync state for incremental sync."""
        self._sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()
        SYNC_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write
        tmp_file = SYNC_STATE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w") as f:
            json.dump(self._sync_state, f, indent=2, ensure_ascii=False)
        tmp_file.replace(SYNC_STATE_FILE)

    def validate_config(self) -> tuple[bool, str]:
        """Check if Hetzner config is valid."""
        if not self.config.host:
            return False, "HETZNER_HOST nicht gesetzt. Bitte in .env konfigurieren."
        if not self.config.username:
            return False, "HETZNER_USER nicht gesetzt. Bitte in .env konfigurieren."
        if not self.config.password and not self.config.ssh_key_path:
            return False, (
                "Weder HETZNER_PASSWORD noch HETZNER_SSH_KEY_PATH gesetzt. "
                "Mindestens eins wird benoetigt."
            )
        if self.config.ssh_key_path and not Path(self.config.ssh_key_path).exists():
            return False, f"SSH Key nicht gefunden: {self.config.ssh_key_path}"
        return True, "OK"

    async def connect(self) -> bool:
        """Establish SFTP connection to Hetzner server."""
        try:
            import paramiko
        except ImportError:
            print("[ERROR] paramiko nicht installiert. Bitte: pip install paramiko")
            return False

        valid, msg = self.validate_config()
        if not valid:
            print(f"[ERROR] Hetzner Config: {msg}")
            return False

        try:
            self._transport = paramiko.Transport((self.config.host, self.config.port))

            if self.config.ssh_key_path:
                # SSH Key Authentication
                key_path = Path(self.config.ssh_key_path).expanduser()
                try:
                    pkey = paramiko.RSAKey.from_private_key_file(str(key_path))
                except paramiko.ssh_exception.SSHException:
                    try:
                        pkey = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    except paramiko.ssh_exception.SSHException:
                        pkey = paramiko.ECDSAKey.from_private_key_file(str(key_path))
                self._transport.connect(username=self.config.username, pkey=pkey)
            else:
                # Password Authentication
                self._transport.connect(
                    username=self.config.username,
                    password=self.config.password,
                )

            self._sftp = paramiko.SFTPClient.from_transport(self._transport)
            print(f"[OK] Verbunden mit Hetzner: {self.config.host}")
            return True

        except Exception as e:
            print(f"[ERROR] Hetzner-Verbindung fehlgeschlagen: {e}")
            return False

    def disconnect(self):
        """Close SFTP connection."""
        if self._sftp:
            self._sftp.close()
        if self._transport:
            self._transport.close()
        self._sftp = None
        self._transport = None

    def _list_remote_files(self, remote_dir: str) -> list[dict]:
        """Recursively list all legal document files in a remote directory."""
        files = []
        if not self._sftp:
            return files

        try:
            entries = self._sftp.listdir_attr(remote_dir)
        except FileNotFoundError:
            return files
        except PermissionError:
            print(f"[WARN] Kein Zugriff auf: {remote_dir}")
            return files

        for entry in entries:
            remote_path = f"{remote_dir}/{entry.filename}"

            if stat.S_ISDIR(entry.st_mode):
                # Recurse into subdirectories
                files.extend(self._list_remote_files(remote_path))
            elif stat.S_ISREG(entry.st_mode):
                ext = Path(entry.filename).suffix.lower()
                if ext in LEGAL_EXTENSIONS:
                    size_mb = entry.st_size / (1024 * 1024)
                    if size_mb <= self.config.max_file_size_mb:
                        files.append({
                            "remote_path": remote_path,
                            "filename": entry.filename,
                            "size_bytes": entry.st_size,
                            "modified_at": datetime.fromtimestamp(
                                entry.st_mtime, tz=timezone.utc
                            ).isoformat(),
                        })
        return files

    def _needs_sync(self, remote_file: dict) -> bool:
        """Check if a remote file needs to be downloaded (new or changed)."""
        key = remote_file["remote_path"]
        if key not in self._sync_state.get("files", {}):
            return True  # New file
        cached = self._sync_state["files"][key]
        if cached.get("size_bytes") != remote_file["size_bytes"]:
            return True  # Size changed
        if cached.get("modified_at") != remote_file["modified_at"]:
            return True  # Modified
        # Check local file still exists
        if not Path(cached.get("local_path", "")).exists():
            return True  # Local file deleted
        return False

    def _compute_sha256(self, filepath: str) -> str:
        """Compute SHA256 hash of a local file."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    async def sync_documents(self, dry_run: bool = False) -> list[SyncedFile]:
        """
        Sync all legal documents from Hetzner to local data/inbox/.

        Args:
            dry_run: If True, only list what would be synced without downloading.

        Returns:
            List of newly synced files.
        """
        if not await self.connect():
            return []

        DATA_INBOX.mkdir(parents=True, exist_ok=True)

        # Discover all remote files
        all_remote_files = []
        for remote_dir in self.config.remote_dirs:
            print(f"[SCAN] Scanne {remote_dir} ...")
            files = self._list_remote_files(remote_dir)
            all_remote_files.extend(files)
            print(f"  -> {len(files)} Dateien gefunden")

        # Filter to files needing sync
        to_sync = [f for f in all_remote_files if self._needs_sync(f)]

        print(f"\n[SYNC] {len(to_sync)} neue/geaenderte Dateien von {len(all_remote_files)} gesamt")

        if dry_run:
            for f in to_sync:
                size_kb = f["size_bytes"] / 1024
                print(f"  [DRY] {f['filename']} ({size_kb:.1f} KB)")
            self.disconnect()
            return []

        # Download files
        synced: list[SyncedFile] = []
        for i, remote_file in enumerate(to_sync, 1):
            filename = remote_file["filename"]
            # Preserve subfolder structure
            rel_path = remote_file["remote_path"].lstrip("/")
            local_path = DATA_INBOX / rel_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"  [{i}/{len(to_sync)}] {filename} ...", end=" ", flush=True)

            try:
                self._sftp.get(remote_file["remote_path"], str(local_path))
                sha256 = self._compute_sha256(str(local_path))

                sf = SyncedFile(
                    remote_path=remote_file["remote_path"],
                    local_path=str(local_path),
                    filename=filename,
                    size_bytes=remote_file["size_bytes"],
                    sha256=sha256,
                    synced_at=datetime.now(timezone.utc).isoformat(),
                    file_type=Path(filename).suffix.lower(),
                    modified_at=remote_file.get("modified_at", ""),
                )
                synced.append(sf)

                # Update sync state
                self._sync_state.setdefault("files", {})[remote_file["remote_path"]] = {
                    "local_path": str(local_path),
                    "size_bytes": remote_file["size_bytes"],
                    "sha256": sha256,
                    "modified_at": remote_file.get("modified_at", ""),
                    "synced_at": sf.synced_at,
                }

                size_kb = remote_file["size_bytes"] / 1024
                print(f"OK ({size_kb:.1f} KB)")

            except Exception as e:
                print(f"FEHLER: {e}")

        self._save_sync_state()
        self.disconnect()

        print(f"\n[DONE] {len(synced)} Dateien synchronisiert nach {DATA_INBOX}")
        return synced

    async def list_remote(self) -> list[dict]:
        """List all remote files without downloading."""
        if not await self.connect():
            return []

        all_files = []
        for remote_dir in self.config.remote_dirs:
            files = self._list_remote_files(remote_dir)
            all_files.extend(files)

        self.disconnect()
        return all_files

    def get_sync_status(self) -> dict:
        """Get current sync status."""
        return {
            "last_sync": self._sync_state.get("last_sync"),
            "total_synced": len(self._sync_state.get("files", {})),
            "files": list(self._sync_state.get("files", {}).keys()),
            "config_valid": self.validate_config()[0],
        }


# ── CLI Interface ─────────────────────────────────────────────────────
async def main():
    """CLI entry point for Hetzner sync."""
    import sys

    connector = HetznerConnector()

    valid, msg = connector.validate_config()
    if not valid:
        print(f"\n[CONFIG ERROR] {msg}")
        print("\nBitte diese Variablen in .env setzen:")
        print("  HETZNER_HOST=your-server.hetzner.de")
        print("  HETZNER_USER=your-username")
        print("  HETZNER_PASSWORD=your-password")
        print("  # ODER:")
        print("  HETZNER_SSH_KEY_PATH=~/.ssh/id_rsa")
        print("  HETZNER_REMOTE_PATH=/legal")
        return

    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"

    if cmd == "status":
        status = connector.get_sync_status()
        print(f"Letzter Sync: {status['last_sync'] or 'Nie'}")
        print(f"Dateien synchronisiert: {status['total_synced']}")
    elif cmd == "list":
        files = await connector.list_remote()
        print(f"\n{len(files)} Dateien auf Hetzner gefunden:")
        for f in files:
            size_kb = f["size_bytes"] / 1024
            print(f"  {f['remote_path']} ({size_kb:.1f} KB)")
    elif cmd == "dry-run":
        await connector.sync_documents(dry_run=True)
    elif cmd == "sync":
        synced = await connector.sync_documents()
        print(f"\nFertig: {len(synced)} Dateien synchronisiert")
    else:
        print("Usage: python -m data.hetzner_connector [sync|list|status|dry-run]")


if __name__ == "__main__":
    asyncio.run(main())
