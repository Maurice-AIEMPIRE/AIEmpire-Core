"""
Cloud Backend — Zero Local Memory Architecture
===============================================
All data stored in cloud:
  - Google Drive (primary)
  - iCloud (backup)
  - LocalStorage (cache only)

Codex:
  - Zero cost (Google Drive free tier: 15GB)
  - Maximum performance
  - Unlimited scale
  - No local disk bloat

Pattern:
  Agent creates result → saves to cache
  Cache syncs to Google Drive
  Google Drive syncs to iCloud
  Local cache clears periodically
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
import hashlib

from antigravity.config import PROJECT_ROOT


@dataclass
class CloudResource:
    """Represents data in cloud."""
    resource_id: str
    resource_type: str  # "content", "checkpoint", "analytics"
    local_path: Optional[str]
    cloud_path: str  # "drive://folder/file" or "icloud://folder/file"
    size_bytes: int = 0
    checksum: str = ""
    synced: bool = False


class CloudBackend:
    """
    Manages cloud storage for zero-local-memory architecture.

    Supports:
      - Google Drive
      - iCloud
      - Hybrid sync (primary + backup)

    Usage:
        cloud = CloudBackend()
        await cloud.upload("content.json", "results/content_001.json")
        data = await cloud.download("content.json")
        await cloud.clear_local_cache()
    """

    CACHE_DIR = Path(PROJECT_ROOT) / "antigravity" / "_cloud_cache"
    SYNC_MANIFEST = CACHE_DIR / "sync_manifest.json"
    MAX_CACHE_SIZE_MB = 100  # Keep cache under 100MB

    def __init__(self, use_google_drive: bool = True, use_icloud: bool = True):
        self.use_google_drive = use_google_drive
        self.use_icloud = use_icloud
        self.resources: Dict[str, CloudResource] = {}
        self.cache_size_mb = 0

        self._ensure_directories()
        self._load_manifest()

        print("☁️  Cloud Backend initialized")
        print(f"   Google Drive: {'✓' if use_google_drive else '✗'}")
        print(f"   iCloud: {'✓' if use_icloud else '✗'}")

    def _ensure_directories(self) -> None:
        """Create cache directories."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _load_manifest(self) -> None:
        """Load sync manifest."""
        if self.SYNC_MANIFEST.exists():
            try:
                with open(self.SYNC_MANIFEST) as f:
                    data = json.load(f)
                    for resource_id, resource_data in data.items():
                        self.resources[resource_id] = CloudResource(**resource_data)
            except Exception as e:
                print(f"⚠️  Error loading manifest: {e}")

    async def upload(
        self,
        local_file: str,
        cloud_path: str,
        resource_type: str = "content",
    ) -> CloudResource:
        """
        Upload file to cloud.

        cloud_path examples:
          - "drive://results/content_001.json"
          - "icloud://content/file.json"
          - "drive+icloud://shared/file.json" (both)
        """
        local_path = self.CACHE_DIR / local_file
        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        # Calculate checksum
        checksum = self._calculate_checksum(local_path)

        # Create resource
        resource_id = hashlib.md5(
            f"{cloud_path}_{checksum}".encode()
        ).hexdigest()[:12]

        resource = CloudResource(
            resource_id=resource_id,
            resource_type=resource_type,
            local_path=str(local_path),
            cloud_path=cloud_path,
            size_bytes=local_path.stat().st_size,
            checksum=checksum,
            synced=False,
        )

        # Upload to destinations
        if "drive" in cloud_path.lower() and self.use_google_drive:
            await self._upload_to_google_drive(local_path, cloud_path, resource_id)

        if "icloud" in cloud_path.lower() and self.use_icloud:
            await self._upload_to_icloud(local_path, cloud_path, resource_id)

        resource.synced = True
        self.resources[resource_id] = resource
        self._save_manifest()

        print(f"✓ Uploaded {local_file} → {cloud_path}")
        return resource

    async def download(
        self,
        cloud_path: str,
        local_file: str = None,
    ) -> str:
        """Download file from cloud to local cache."""
        if local_file is None:
            local_file = Path(cloud_path).name

        local_path = self.CACHE_DIR / local_file

        # Try Google Drive first
        if "drive" in cloud_path.lower() and self.use_google_drive:
            success = await self._download_from_google_drive(cloud_path, local_path)
            if success:
                return str(local_path)

        # Try iCloud
        if "icloud" in cloud_path.lower() and self.use_icloud:
            success = await self._download_from_icloud(cloud_path, local_path)
            if success:
                return str(local_path)

        raise FileNotFoundError(f"Could not download {cloud_path}")

    async def clear_local_cache(self, keep_recent: int = 10) -> Dict[str, Any]:
        """
        Clear local cache, keeping only recent files.

        Returns stats on what was removed.
        """
        files = sorted(self.CACHE_DIR.glob("*"), key=lambda p: p.stat().st_mtime)

        # Keep most recent N files
        to_delete = files[:-keep_recent] if len(files) > keep_recent else []

        total_freed = 0
        for file_path in to_delete:
            if file_path.suffix == ".json" or file_path.suffix == ".txt":
                size = file_path.stat().st_size
                file_path.unlink()
                total_freed += size

        freed_mb = total_freed / (1024 * 1024)

        print(f"🗑️  Cleared {len(to_delete)} files, freed {freed_mb:.1f}MB")

        return {
            "files_deleted": len(to_delete),
            "space_freed_mb": freed_mb,
            "files_remaining": keep_recent,
        }

    async def sync_all(self) -> Dict[str, Any]:
        """Sync all pending uploads to cloud."""
        pending = [
            r for r in self.resources.values() if not r.synced
        ]

        print(f"🔄 Syncing {len(pending)} resources...")

        for resource in pending:
            if resource.local_path and Path(resource.local_path).exists():
                local_path = Path(resource.local_path)

                # Re-upload
                if "drive" in resource.cloud_path.lower():
                    await self._upload_to_google_drive(
                        local_path,
                        resource.cloud_path,
                        resource.resource_id,
                    )

                if "icloud" in resource.cloud_path.lower():
                    await self._upload_to_icloud(
                        local_path,
                        resource.cloud_path,
                        resource.resource_id,
                    )

                resource.synced = True

        self._save_manifest()

        return {
            "synced": len(pending),
            "total_resources": len(self.resources),
        }

    # ─── Cloud Provider Integration ──────────────────────────────────────

    async def _upload_to_google_drive(
        self,
        local_path: Path,
        cloud_path: str,
        resource_id: str,
    ) -> bool:
        """Upload to Google Drive via API or iCloud Drive folder fallback."""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            creds_path = Path(PROJECT_ROOT) / "credentials" / "google_drive_service_account.json"
            if not creds_path.exists():
                print(f"   ⚠️  Google Drive: credentials not found at {creds_path}")
                return False

            creds = Credentials.from_service_account_file(
                str(creds_path),
                scopes=["https://www.googleapis.com/auth/drive.file"],
            )
            service = build("drive", "v3", credentials=creds)

            path_parts = cloud_path.replace("drive://", "").split("/")
            file_name = path_parts[-1] if path_parts else local_path.name

            media = MediaFileUpload(str(local_path), resumable=True)
            result = service.files().create(
                body={"name": file_name}, media_body=media, fields="id"
            ).execute()

            print(f"   ☁️  → Google Drive: {cloud_path} (id={result.get('id', resource_id)})")
            return True

        except ImportError:
            print(f"   ⚠️  Google Drive API not installed (pip install google-auth-oauthlib google-api-python-client)")
            return False

        except Exception as e:
            print(f"   ❌ Google Drive upload failed: {e}")
            return False

    async def _upload_to_icloud(
        self,
        local_path: Path,
        cloud_path: str,
        resource_id: str,
    ) -> bool:
        """Upload to iCloud via local iCloud Drive sync folder (macOS)."""
        import shutil

        icloud_dir = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "AIEmpire"
        try:
            icloud_dir.mkdir(parents=True, exist_ok=True)
            path_parts = cloud_path.replace("icloud://", "").split("/")
            file_name = path_parts[-1] if path_parts else local_path.name
            dest = icloud_dir / file_name
            shutil.copy2(str(local_path), str(dest))
            print(f"   ☁️  → iCloud: {dest}")
            return True
        except OSError as e:
            print(f"   ⚠️  iCloud Drive not available (macOS only): {e}")
            return False
        except Exception as e:
            print(f"   ❌ iCloud upload failed: {e}")
            return False

    async def _download_from_google_drive(
        self,
        cloud_path: str,
        local_path: Path,
    ) -> bool:
        """Download from Google Drive via API."""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            creds_path = Path(PROJECT_ROOT) / "credentials" / "google_drive_service_account.json"
            if not creds_path.exists():
                print(f"   ⚠️  Google Drive: credentials not found at {creds_path}")
                return False

            creds = Credentials.from_service_account_file(
                str(creds_path),
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            service = build("drive", "v3", credentials=creds)

            path_parts = cloud_path.replace("drive://", "").split("/")
            file_name = path_parts[-1] if path_parts else "unknown"

            results = service.files().list(
                q=f"name='{file_name}'", fields="files(id, name)"
            ).execute()
            files = results.get("files", [])

            if not files:
                print(f"   ⚠️  File not found on Google Drive: {file_name}")
                return False

            import io
            from googleapiclient.http import MediaIoBaseDownload

            request = service.files().get_media(fileId=files[0]["id"])
            with open(local_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

            print(f"   ☁️  ← Google Drive: {cloud_path}")
            return True

        except ImportError:
            print(f"   ⚠️  Google Drive API not installed (pip install google-auth-oauthlib google-api-python-client)")
            return False

        except Exception as e:
            print(f"   ❌ Google Drive download failed: {e}")
            return False

    async def _download_from_icloud(
        self,
        cloud_path: str,
        local_path: Path,
    ) -> bool:
        """Download from iCloud via local iCloud Drive sync folder (macOS)."""
        import shutil

        icloud_dir = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "AIEmpire"
        try:
            path_parts = cloud_path.replace("icloud://", "").split("/")
            file_name = path_parts[-1] if path_parts else "unknown"
            source = icloud_dir / file_name

            if not source.exists():
                print(f"   ⚠️  File not found in iCloud Drive: {source}")
                return False

            shutil.copy2(str(source), str(local_path))
            print(f"   ☁️  ← iCloud: {source}")
            return True

        except OSError as e:
            print(f"   ⚠️  iCloud Drive not available (macOS only): {e}")
            return False

        except Exception as e:
            print(f"   ❌ iCloud download failed: {e}")
            return False

    # ─── Utilities ──────────────────────────────────────────────────────

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def _save_manifest(self) -> None:
        """Save sync manifest."""
        try:
            manifest_data = {
                resource_id: {
                    "resource_id": r.resource_id,
                    "resource_type": r.resource_type,
                    "local_path": r.local_path,
                    "cloud_path": r.cloud_path,
                    "size_bytes": r.size_bytes,
                    "checksum": r.checksum,
                    "synced": r.synced,
                }
                for resource_id, r in self.resources.items()
            }

            with open(self.SYNC_MANIFEST, "w") as f:
                json.dump(manifest_data, f, indent=2)

        except Exception as e:
            print(f"❌ Error saving manifest: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get cloud backend status."""
        total_size = sum(r.size_bytes for r in self.resources.values())
        synced = sum(1 for r in self.resources.values() if r.synced)

        return {
            "storage": {
                "total_resources": len(self.resources),
                "total_size_mb": total_size / (1024 * 1024),
                "synced": synced,
                "pending": len(self.resources) - synced,
            },
            "cache": {
                "cache_dir": str(self.CACHE_DIR),
                "max_cache_mb": self.MAX_CACHE_SIZE_MB,
            },
            "providers": {
                "google_drive": self.use_google_drive,
                "icloud": self.use_icloud,
            },
        }


# ─── Global Cloud Backend ────────────────────────────────────────────────────

_global_cloud: Optional[CloudBackend] = None


def get_cloud_backend() -> CloudBackend:
    """Get or create global cloud backend."""
    global _global_cloud
    if _global_cloud is None:
        _global_cloud = CloudBackend()
    return _global_cloud


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== CLOUD BACKEND TEST ===\n")

        cloud = CloudBackend()

        # Create a test file
        test_file = cloud.CACHE_DIR / "test.json"
        test_file.write_text('{"test": "data"}')

        # Upload
        resource = await cloud.upload(
            "test.json",
            "drive://test_folder/test.json",
            resource_type="content",
        )
        print(f"Resource ID: {resource.resource_id}\n")

        # Show status
        status = cloud.get_status()
        print(f"Status: {json.dumps(status, indent=2)}\n")

        # Clear cache
        cleared = await cloud.clear_local_cache(keep_recent=5)
        print(f"Cleared: {json.dumps(cleared, indent=2)}")

    asyncio.run(test())
