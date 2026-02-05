from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROUTER_CONFIG = ROOT / "automation" / "config" / "router.json"
DEFAULT_SYSTEM_CONFIG = ROOT / "automation" / "config" / "defaults.json"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_router_config(path: Optional[Path] = None) -> Dict[str, Any]:
    cfg_path = path or DEFAULT_ROUTER_CONFIG
    return load_json(cfg_path)


def load_system_config(path: Optional[Path] = None) -> Dict[str, Any]:
    cfg_path = path or DEFAULT_SYSTEM_CONFIG
    return load_json(cfg_path)
