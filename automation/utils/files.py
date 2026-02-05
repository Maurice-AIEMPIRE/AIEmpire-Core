from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional


def timestamp_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def backup_file(path: Path, backup_dir: Path) -> Optional[Path]:
    if not path.exists():
        return None
    ensure_dir(backup_dir)
    dest = backup_dir / path.name
    shutil.copy2(path, dest)
    return dest


def env_or_default(key: str, default: Optional[str] = None) -> Optional[str]:
    value = os.environ.get(key)
    if value is None or value.strip() == "":
        return default
    return value.strip()



_slug_re = None


def slugify(value: str, max_len: int = 80) -> str:
    import re
    global _slug_re
    if _slug_re is None:
        _slug_re = re.compile(r"[^a-zA-Z0-9]+")
    slug = _slug_re.sub("-", value.strip().lower()).strip("-")
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return slug or "note"
