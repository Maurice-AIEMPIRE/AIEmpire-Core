#!/usr/bin/env python3
"""
Canonical infrastructure/runtime audit for AI Empire.

Modes:
- snapshot: collect current state and write JSON inventory
- verify: validate existing inventory schema (or in-memory snapshot)
"""

from __future__ import annotations

import argparse
import json
import os
import pwd
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
UID = os.getuid()
DEBUG = os.getenv("AUDIT_DEBUG", "0").strip() == "1"

DEFAULT_OUTPUT = ROOT / "00_SYSTEM/infra/SYSTEM_INVENTORY_2026-02-18.json"

ENV_FILES = [
    ROOT / ".env",
    ROOT / "automation/.env",
    Path.home() / ".openclaw/.env",
    Path.home() / ".openclaw/workspace/ai-empire/.env",
    Path.home() / "Library/Application Support/ai-empire/automation/.env",
    Path.home() / "Library/Application Support/ai-empire/legion-runtime/automation/.env",
    Path.home() / ".zshrc",
]

KEY_GROUPS = {
    "youtube": [
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
        "YOUTUBE_REFRESH_TOKEN",
        "YOUTUBE_ACCESS_TOKEN",
        "YOUTUBE_API_KEY",
    ],
    "stripe": ["STRIPE_SECRET_KEY"],
    "telegram": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
    "n8n": ["N8N_API_KEY", "KIMI_N8N_API_KEY"],
    "gumroad": ["GUMROAD_ACCESS_TOKEN"],
    "tiktok": [
        "TIKTOK_CLIENT_KEY",
        "TIKTOK_CLIENT_SECRET",
        "TIKTOK_ACCESS_TOKEN",
        "TIKTOK_REFRESH_TOKEN",
    ],
}

ENDPOINTS = [
    {"name": "n8n_health", "url": "http://localhost:5678/healthz"},
    {"name": "ollama_tags", "url": "http://localhost:11434/api/tags"},
    {"name": "openclaw_gateway", "url": "http://localhost:18789/"},
    {"name": "empire_api", "url": "http://localhost:3333"},
    {"name": "store_ui", "url": "http://localhost:5001"},
    {"name": "openclaw_api", "url": "http://localhost:8080/health"},
]

ICLOUD_CLUSTERS = [
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI_EMPIRE_STORAGE"),
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI_Empire_Revenue"),
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI_Empire_Backup"),
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI_EMPIRE_BACKUP"),
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI-Empire-Backup"),
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI_Empire_Backups"),
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI_Empire_TikTok"),
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI_Empire_Swarm"),
    Path("/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs/AI_Empire_Monster"),
]

WATCH_LABEL_RE = re.compile(
    r"(ai-empire|openclaw|youtube|telegram|n8n|guardian|agentmonitor|aiempire)", re.IGNORECASE
)
SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"\b([A-Z0-9_]*(?:TOKEN|SECRET|KEY|PASSWORD|API_KEY)[A-Z0-9_]*)=([^\s]+)"
)
PREFERRED_LABELS = [
    "com.ai-empire.watchdog",
    "com.ai-empire.snapshot",
    "com.ai-empire.autonomy",
    "com.ai-empire.n8n",
    "com.ai-empire.legion50",
    "com.ai-empire.openclaw-self-heal",
    "com.ai-empire.openclaw-snapshot",
    "com.ai-empire.telegram-router",
    "com.ai-empire.master-chat-controller",
    "ai-empire.youtube-automation.godmode",
    "com.empire.youtube.producer",
    "ai.openclaw.gateway",
    "com.aiempire.guardian",
    "com.ai-empire.daily-content-sprint",
    "com.ai-empire.chat-export-ingest",
    "com.ai-empire.shorts-revenue",
    "com.ai-empire.income-stream",
    "com.ai-empire.telegram-report",
    "com.ai-empire.infra-audit-daily",
]
CRITICAL_LABELS = [
    "com.ai-empire.watchdog",
    "com.ai-empire.autonomy",
    "com.ai-empire.n8n",
    "com.ai-empire.master-chat-controller",
    "com.ai-empire.telegram-router",
    "ai-empire.youtube-automation.godmode",
    "com.empire.youtube.producer",
    "com.ai-empire.snapshot",
]

FUNCTION_GROUP_RULES: dict[str, str] = {
    "watchdog": "watchdog",
    "autonomy": "orchestrator",
    "master-chat-controller": "orchestrator",
    "telegram-router": "telegram_router",
    "telegram-report": "telegram_router",
    "youtube-automation.godmode": "youtube_autopilot",
    "youtube.producer": "youtube_autopilot",
    "youtube-shorts": "youtube_autopilot",
    "n8n": "n8n",
    "snapshot": "snapshot",
    "openclaw": "openclaw_gateway",
    "infra-audit": "infra_audit",
}

CANONICAL_LABELS: dict[str, str] = {
    "orchestrator": "com.ai-empire.autonomy",
    "watchdog": "com.ai-empire.watchdog",
    "openclaw_gateway": "ai.openclaw.gateway",
    "telegram_router": "com.ai-empire.telegram-router",
    "youtube_autopilot": "ai-empire.youtube-automation.godmode",
    "n8n": "com.ai-empire.n8n",
    "snapshot": "com.ai-empire.snapshot",
    "infra_audit": "com.ai-empire.infra-audit-daily",
}

GROUP_ENDPOINT_DEPS: dict[str, list[str]] = {
    "openclaw_gateway": ["http://localhost:18789/", "http://localhost:8080/health"],
    "n8n": ["http://localhost:5678/healthz"],
    "youtube_autopilot": ["http://localhost:11434/api/tags"],
}

HEAVY_GROUPS = {"orchestrator", "youtube_autopilot", "openclaw_gateway"}
DEFAULT_WINDOW_POLICY = "08:00-23:00"


@dataclass
class CmdResult:
    code: int
    out: str
    err: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def debug(msg: str) -> None:
    if DEBUG:
        print(f"[audit][debug] {msg}", flush=True)


def run(cmd: list[str], timeout: int = 15) -> CmdResult:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return CmdResult(p.returncode, p.stdout, p.stderr)
    except Exception as exc:  # noqa: BLE001
        return CmdResult(1, "", str(exc))


def run_shell(cmd: str, timeout: int = 20) -> CmdResult:
    return run(["/bin/zsh", "-lc", cmd], timeout=timeout)


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_kv(raw: str, key: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+)$", raw, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip()


def file_exists(path: str | None) -> bool:
    if not path:
        return False
    p = Path(path).expanduser()
    return p.exists()


def parent_exists(path: str | None) -> bool:
    if not path:
        return False
    p = Path(path).expanduser()
    return p.parent.exists()


def maybe_command_exists(program: str | None) -> bool:
    if not program:
        return False
    if program.startswith("/"):
        return Path(program).exists()
    return shutil.which(program) is not None


def infer_function_group(label: str) -> str:
    lowered = label.lower()
    for token, group in FUNCTION_GROUP_RULES.items():
        if token in lowered:
            return group
    return "other"


def window_policy_for_group(group: str) -> str:
    if group in HEAVY_GROUPS:
        return DEFAULT_WINDOW_POLICY
    return "always"


def owner_stack_for_job(source_plist: str | None) -> str:
    source = (source_plist or "").lower()
    if "openclaw" in source:
        return "openclaw_workspace"
    if "new project" in source:
        return "new_project"
    if "ai_agents" in source:
        return "ai_agents"
    return "unknown"


def classify_job_state(loaded_state: str | None, last_exit_code: str | None) -> str:
    ls = (loaded_state or "").lower()
    ec = str(last_exit_code or "")
    if "running" in ls:
        return "running"
    if "not-loaded" in ls:
        return "not_loaded"
    if "78" in ec:
        return "error_ex_config"
    if ec and ec not in {"0", "(never exited)"}:
        return "error_nonzero_exit"
    if ls:
        return ls
    return "unknown"


def collect_labels() -> list[str]:
    res = run(["launchctl", "list"])
    labels: list[str] = []
    for line in res.out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"\s+", line)
        if len(parts) < 3:
            continue
        label = parts[-1]
        if WATCH_LABEL_RE.search(label):
            labels.append(label)
    label_set = set(labels)
    # Keep runtime bounded and deterministic: always include preferred labels first.
    ordered = list(PREFERRED_LABELS)
    # Add up to 40 extra matching labels.
    extras = sorted(label_set - set(ordered))[:40]
    return ordered + extras


def collect_job(label: str) -> dict[str, Any]:
    raw = run(["launchctl", "print", f"gui/{UID}/{label}"], timeout=4)
    if raw.code != 0:
        guessed_plist = Path.home() / "Library/LaunchAgents" / f"{label}.plist"
        source_plist = str(guessed_plist) if guessed_plist.exists() else None
        function_group = infer_function_group(label)
        return {
            "label": label,
            "function_group": function_group,
            "canonical": CANONICAL_LABELS.get(function_group) == label,
            "disabled_reason": "launchctl_print_failed",
            "depends_on_endpoints": GROUP_ENDPOINT_DEPS.get(function_group, []),
            "window_policy": window_policy_for_group(function_group),
            "owner_stack": owner_stack_for_job(source_plist),
            "state": "not_loaded",
            "source_plist": source_plist,
            "loaded_state": "not-loaded",
            "last_exit_code": None,
            "program": None,
            "stdout_path": None,
            "stderr_path": None,
            "exists_flags": {
                "source_plist_exists": bool(source_plist),
                "program_exists": False,
                "stdout_parent_exists": False,
                "stderr_parent_exists": False,
            },
            "runs": None,
            "pid": None,
            "notes": raw.err.strip() or "launchctl print failed",
        }

    source_plist = parse_kv(raw.out, "path")
    loaded_state = parse_kv(raw.out, "state")
    last_exit_code = parse_kv(raw.out, "last exit code")
    program = parse_kv(raw.out, "program")
    stdout_path = parse_kv(raw.out, "stdout path")
    stderr_path = parse_kv(raw.out, "stderr path")
    runs = parse_kv(raw.out, "runs")
    pid = parse_kv(raw.out, "pid")
    function_group = infer_function_group(label)

    return {
        "label": label,
        "function_group": function_group,
        "canonical": CANONICAL_LABELS.get(function_group) == label,
        "disabled_reason": None,
        "depends_on_endpoints": GROUP_ENDPOINT_DEPS.get(function_group, []),
        "window_policy": window_policy_for_group(function_group),
        "owner_stack": owner_stack_for_job(source_plist),
        "state": classify_job_state(loaded_state, last_exit_code),
        "source_plist": source_plist,
        "loaded_state": loaded_state,
        "last_exit_code": last_exit_code,
        "program": program,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "exists_flags": {
            "source_plist_exists": file_exists(source_plist),
            "program_exists": maybe_command_exists(program),
            "stdout_parent_exists": parent_exists(stdout_path),
            "stderr_parent_exists": parent_exists(stderr_path),
        },
        "runs": int(runs) if runs and runs.isdigit() else runs,
        "pid": int(pid) if pid and pid.isdigit() else pid,
    }


def collect_jobs() -> list[dict[str, Any]]:
    return [collect_job(label) for label in collect_labels()]


def redact_process_line(line: str, redact: bool) -> str:
    if not redact:
        return line
    return SENSITIVE_ASSIGNMENT_RE.sub(r"\1=<redacted>", line)


def process_lines(pattern: str, redact: bool) -> list[str]:
    matches: dict[str, bool] = {}
    tokens = [p.strip() for p in pattern.split("|") if p.strip()]
    for token in tokens:
        res = run(["pgrep", "-fl", token], timeout=2)
        for ln in res.out.splitlines():
            line = ln.strip()
            if line:
                matches[redact_process_line(line, redact)] = True
    return sorted(matches.keys())[:300]


def probe_endpoint(url: str, redact: bool) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": "ai-empire-audit/1.0"})
    result: dict[str, Any] = {"url": url, "status_code": 0, "ok": False, "error": None}
    try:
        with urlopen(req, timeout=4) as resp:  # noqa: S310
            body = resp.read(300).decode("utf-8", errors="replace")
            result["status_code"] = resp.status
            result["ok"] = 200 <= resp.status < 400
            result["preview"] = "<redacted>" if redact else body
    except HTTPError as exc:
        result["status_code"] = exc.code
        result["error"] = f"http_error:{exc.code}"
    except URLError as exc:
        result["error"] = f"url_error:{exc.reason}"
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
    return result


def parse_env_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    if not path.exists() or not path.is_file():
        return keys
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            name = line.split("=", 1)[0].strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                keys.add(name)
    except Exception:  # noqa: BLE001
        pass
    return keys


def probe_env_file_with_timeout(path: Path, timeout: int = 6) -> dict[str, Any]:
    script = (
        "import json,re,sys\n"
        "from pathlib import Path\n"
        "p=Path(sys.argv[1]).expanduser()\n"
        "res={'exists':False,'is_file':False,'keys':[],'error':None}\n"
        "try:\n"
        "  res['exists']=p.exists()\n"
        "  if res['exists'] and p.is_file():\n"
        "    res['is_file']=True\n"
        "    txt=p.read_text(encoding='utf-8', errors='ignore')\n"
        "    ks=[]\n"
        "    for line in txt.splitlines():\n"
        "      s=line.strip()\n"
        "      if not s or s.startswith('#') or '=' not in s:\n"
        "        continue\n"
        "      name=s.split('=',1)[0].strip()\n"
        "      if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):\n"
        "        ks.append(name)\n"
        "    res['keys']=sorted(set(ks))\n"
        "except Exception as e:\n"
        "  res['error']=str(e)\n"
        "print(json.dumps(res))\n"
    )
    probe = run(["python3", "-c", script, str(path)], timeout=timeout)
    if probe.code != 0:
        return {
            "exists": None,
            "is_file": None,
            "keys": [],
            "error": probe.err.strip() or "probe_failed_or_timeout",
        }
    try:
        data = json.loads(probe.out)
    except Exception:  # noqa: BLE001
        return {
            "exists": None,
            "is_file": None,
            "keys": [],
            "error": "probe_output_parse_error",
        }
    if not isinstance(data, dict):
        return {
            "exists": None,
            "is_file": None,
            "keys": [],
            "error": "probe_output_invalid_type",
        }
    return {
        "exists": data.get("exists"),
        "is_file": data.get("is_file"),
        "keys": data.get("keys", []),
        "error": data.get("error"),
    }


def collect_credentials() -> dict[str, Any]:
    file_status: dict[str, Any] = {}
    all_keys_present: set[str] = set(os.environ.keys())

    for path in ENV_FILES:
        timeout = 8 if ".openclaw" in str(path) else 4
        probe = probe_env_file_with_timeout(path, timeout=timeout)
        keyset = set(probe.get("keys", []))
        all_keys_present |= keyset
        file_status[str(path)] = {
            "exists": probe.get("exists"),
            "keys_detected": len(keyset),
            "present_keys": sorted(keyset),
            "scan_error": probe.get("error"),
        }

    group_status: dict[str, Any] = {}
    for group, keys in KEY_GROUPS.items():
        details = {k: ("present" if k in all_keys_present else "missing") for k in keys}
        group_status[group] = {
            "required_keys": keys,
            "status": details,
            "all_present": all(v == "present" for v in details.values()),
            "present_count": sum(v == "present" for v in details.values()),
            "missing_count": sum(v == "missing" for v in details.values()),
        }

    return {
        "files": file_status,
        "groups": group_status,
        "policy": "values never persisted; present/missing only",
    }


def read_json(path: Path) -> dict[str, Any] | None:
    script = (
        "import json,sys\n"
        "from pathlib import Path\n"
        "p=Path(sys.argv[1]).expanduser()\n"
        "res={'exists':False,'data':None,'error':None}\n"
        "try:\n"
        "  if p.exists() and p.is_file():\n"
        "    res['exists']=True\n"
        "    res['data']=json.loads(p.read_text(encoding='utf-8', errors='ignore'))\n"
        "except Exception as e:\n"
        "  res['error']=str(e)\n"
        "print(json.dumps(res))\n"
    )
    probe = run(["python3", "-c", script, str(path)], timeout=4)
    if probe.code != 0:
        return None
    try:
        data = json.loads(probe.out)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(data, dict):
        return None
    if not data.get("exists"):
        return None
    payload = data.get("data")
    return payload if isinstance(payload, dict) else None


def collect_pipeline_state() -> dict[str, Any]:
    ys = read_json(ROOT / "content_factory/deliverables/youtube_shorts/latest.json")
    sr = read_json(ROOT / "content_factory/deliverables/shorts_revenue/latest.json")
    stripe = read_json(ROOT / "content_factory/deliverables/revenue/stripe/latest.json")

    return {
        "youtube_shorts_latest": ys,
        "shorts_revenue_latest": sr,
        "stripe_latest": stripe,
        "stripe_latest_exists": bool(stripe),
    }


def collect_icloud_sizes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in ICLOUD_CLUSTERS:
        probe_script = (
            "import json,sys\n"
            "from pathlib import Path\n"
            "p=Path(sys.argv[1]).expanduser()\n"
            "res={'exists':False,'entry_count':None,'error':None}\n"
            "try:\n"
            "  if p.exists() and p.is_dir():\n"
            "    res['exists']=True\n"
            "    try:\n"
            "      res['entry_count']=sum(1 for _ in p.iterdir())\n"
            "    except Exception as e:\n"
            "      res['error']=str(e)\n"
            "except Exception as e:\n"
            "  res['error']=str(e)\n"
            "print(json.dumps(res))\n"
        )
        probe = run(["python3", "-c", probe_script, str(p)], timeout=3)
        exists = None
        entry_count = None
        if probe.code == 0:
            try:
                out = json.loads(probe.out)
                exists = out.get("exists")
                entry_count = out.get("entry_count")
            except Exception:  # noqa: BLE001
                exists = None
                entry_count = None
        rows.append(
            {
                "path": str(p),
                "exists": exists,
                "size_human": None,
                "top_level_entries": entry_count,
            }
        )
    return rows


def parse_income_report() -> dict[str, Any]:
    report_dir = ROOT / "ai-vault/reports"
    script = (
        "import json,re,sys\n"
        "from pathlib import Path\n"
        "d=Path(sys.argv[1]).expanduser()\n"
        "res={'latest_report':None,'real_revenue_eur':None,'real_gross_eur':None,'successful_payments':None,'projected_revenue_eur_24h':None,'shorts_published_this_run':None,'error':None}\n"
        "try:\n"
        "  if d.exists() and d.is_dir():\n"
        "    files=sorted(d.glob('income_stream_*.txt'))\n"
        "    if files:\n"
        "      p=files[-1]\n"
        "      t=p.read_text(encoding='utf-8', errors='ignore')\n"
        "      res['latest_report']=str(p)\n"
        "      net=re.search(r'Net revenue \\(lookback\\): EUR\\s*([0-9.]+)', t)\n"
        "      gross=re.search(r'Gross revenue \\(lookback\\): EUR\\s*([0-9.]+)', t)\n"
        "      paid=re.search(r'Successful payments:\\s*([0-9]+)', t)\n"
        "      proj=re.search(r'projected revenue 24h:\\s*EUR\\s*([0-9.]+)', t)\n"
        "      ytpub=re.search(r'shorts_revenue published this run:\\s*([0-9]+)', t)\n"
        "      if net: res['real_revenue_eur']=float(net.group(1))\n"
        "      if gross: res['real_gross_eur']=float(gross.group(1))\n"
        "      if paid: res['successful_payments']=int(paid.group(1))\n"
        "      if proj: res['projected_revenue_eur_24h']=float(proj.group(1))\n"
        "      if ytpub: res['shorts_published_this_run']=int(ytpub.group(1))\n"
        "except Exception as e:\n"
        "  res['error']=str(e)\n"
        "print(json.dumps(res))\n"
    )
    probe = run(["python3", "-c", script, str(report_dir)], timeout=5)
    if probe.code != 0:
        return {"latest_report": None, "error": probe.err.strip() or "income_report_probe_failed"}
    try:
        data = json.loads(probe.out)
    except Exception:  # noqa: BLE001
        return {"latest_report": None, "error": "income_report_probe_parse_error"}
    return data if isinstance(data, dict) else {"latest_report": None}


def build_gaps(jobs: list[dict[str, Any]], creds: dict[str, Any], pipelines: dict[str, Any], revenue: dict[str, Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []

    for j in jobs:
        if j.get("label") in CRITICAL_LABELS and j.get("loaded_state") == "not-loaded":
            gaps.append(
                {
                    "id": f"job_not_loaded::{j['label']}",
                    "priority": "P0",
                    "type": "runtime",
                    "summary": f"Critical LaunchAgent is not loaded: {j['label']}",
                    "evidence": {
                        "label": j["label"],
                        "source_plist": j.get("source_plist"),
                    },
                }
            )
        exit_code = str(j.get("last_exit_code") or "")
        if "78" in exit_code:
            gaps.append(
                {
                    "id": f"job_exit_78::{j['label']}",
                    "priority": "P0",
                    "type": "runtime",
                    "summary": f"LaunchAgent exits with EX_CONFIG (78): {j['label']}",
                    "evidence": {
                        "label": j["label"],
                        "last_exit_code": j.get("last_exit_code"),
                        "source_plist": j.get("source_plist"),
                    },
                }
            )

    for group, data in creds.get("groups", {}).items():
        if not data.get("all_present"):
            prio = "P0" if group in {"youtube", "stripe"} else "P1"
            gaps.append(
                {
                    "id": f"credentials::{group}",
                    "priority": prio,
                    "type": "credentials",
                    "summary": f"Required credentials incomplete for {group}",
                    "evidence": data,
                }
            )

    if not pipelines.get("stripe_latest_exists"):
        gaps.append(
            {
                "id": "stripe_source_of_truth_missing",
                "priority": "P0",
                "type": "revenue",
                "summary": "Stripe latest revenue artifact missing",
                "evidence": {
                    "path": str(ROOT / "content_factory/deliverables/revenue/stripe/latest.json"),
                },
            }
        )

    if revenue.get("real_revenue_eur") in {None, 0.0}:
        gaps.append(
            {
                "id": "real_revenue_zero_or_unknown",
                "priority": "P0",
                "type": "revenue",
                "summary": "No real Stripe cashflow recorded in latest income stream report",
                "evidence": revenue,
            }
        )

    if (revenue.get("shorts_published_this_run") or 0) == 0:
        gaps.append(
            {
                "id": "shorts_publish_zero",
                "priority": "P1",
                "type": "distribution",
                "summary": "Latest income report shows zero Shorts publishes",
                "evidence": revenue,
            }
        )

    return gaps


def build_recommendations(gaps: list[dict[str, Any]]) -> list[str]:
    recs: list[str] = []
    if any(g["id"].startswith("job_not_loaded::") for g in gaps):
        recs.append("Load critical LaunchAgents from canonical plists and validate with launchctl print (state=running, last exit code=0).")
    if any(g["id"].startswith("job_exit_78") for g in gaps):
        recs.append("Rebootstrap all EX_CONFIG LaunchAgents from canonical ~/Library/LaunchAgents plists and verify log path validity.")
    if any(g["id"].startswith("credentials::youtube") for g in gaps):
        recs.append("Complete YouTube OAuth env set (client id/secret/refresh token) before enabling public auto-publish.")
    if any(g["id"].startswith("credentials::stripe") for g in gaps):
        recs.append("Set STRIPE_SECRET_KEY and run scheduled stripe sync to establish real cash source-of-truth.")
    if any(g["id"] == "shorts_publish_zero" for g in gaps):
        recs.append("Tune safety guard thresholds and cadence to avoid full skip loops in shorts autopilot.")
    if any(g["id"].startswith("credentials::n8n") for g in gaps):
        recs.append("Set N8N_API_KEY for workflow API validation and lifecycle checks.")
    if not recs:
        recs.append("No critical gaps detected; continue daily audit and weekly consolidation report.")
    return recs


def derive_blockers(gaps: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    revenue = [g for g in gaps if g.get("type") in {"revenue", "credentials"}]
    runtime = [g for g in gaps if g.get("type") == "runtime"]
    return revenue, runtime


def calculate_health_score(jobs: list[dict[str, Any]], endpoints: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> int:
    total_jobs = len(jobs) or 1
    running_or_ok = 0
    for j in jobs:
        state = str(j.get("state") or "")
        ec = str(j.get("last_exit_code") or "")
        if state == "running" or ec in {"0", "(never exited)"}:
            running_or_ok += 1

    endpoint_total = len(endpoints) or 1
    endpoint_ok = sum(1 for e in endpoints if e.get("ok"))
    p0_count = sum(1 for g in gaps if g.get("priority") == "P0")

    score = 100
    score -= int((1 - (running_or_ok / total_jobs)) * 40)
    score -= int((1 - (endpoint_ok / endpoint_total)) * 30)
    score -= min(30, p0_count * 5)
    return max(0, min(100, score))


def collect_snapshot(redact_secrets: bool) -> dict[str, Any]:
    debug("collect_jobs")
    jobs = collect_jobs()
    debug("collect_credentials")
    creds = collect_credentials()
    debug("collect_pipeline_state")
    pipelines = collect_pipeline_state()
    debug("parse_income_report")
    revenue = parse_income_report()
    debug("probe_endpoints")

    endpoints: list[dict[str, Any]] = []
    for e in ENDPOINTS:
        debug(f"probe_endpoint:{e['name']}")
        endpoints.append(
            {
                "name": e["name"],
                **probe_endpoint(e["url"], redact=redact_secrets),
            }
        )

    ps_key = process_lines(
        "icloud_sync_master.py|revenue_generator.py|system_optimizer.py|storage_manager.py|visionary_revenue_agent.py|n8n start|ollama serve|openclaw|empire_autonomy|empire_watchdog|god_mode_daemon|youtube_producer|telegram_router.py|run_legion_50|run_daily_content_sprint|openclaw_self_heal|openclaw_snapshot",
        redact=redact_secrets,
    )
    debug("docker_ps")

    docker = run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"], timeout=10)
    gaps = build_gaps(jobs, creds, pipelines, revenue)
    debug("build_payload")

    revenue_blockers, runtime_blockers = derive_blockers(gaps)
    payload: dict[str, Any] = {
        "generated_at": utc_now(),
        "hosts": {
            "hostname": socket.gethostname(),
            "username": pwd.getpwuid(UID).pw_name,
            "uid": UID,
            "timezone": datetime.now().astimezone().tzname(),
            "project_root": str(ROOT),
        },
        "runtimes": {
            "process_matches": ps_key,
            "docker": {
                "available": shutil.which("docker") is not None,
                "entries": [ln for ln in docker.out.splitlines() if ln.strip()],
            },
            "icloud_clusters": collect_icloud_sizes(),
        },
        "jobs": jobs,
        "endpoints": endpoints,
        "credentials": creds,
        "pipelines": pipelines,
        "revenue": {
            "real_revenue_eur": revenue.get("real_revenue_eur"),
            "projected_revenue_eur_24h": revenue.get("projected_revenue_eur_24h"),
            "publish_counts": {
                "shorts_published_this_run": revenue.get("shorts_published_this_run"),
            },
            "api_usage_flags": {
                "shorts_used_youtube_api": ((pipelines.get("shorts_revenue_latest") or {}).get("used_youtube_api")),
                "shorts_used_tiktok_api": ((pipelines.get("shorts_revenue_latest") or {}).get("used_tiktok_api")),
                "youtube_shorts_used_api": ((pipelines.get("youtube_shorts_latest") or {}).get("used_youtube_api")),
            },
            "income_stream_report": revenue,
        },
        "gaps": gaps,
        "health_score": calculate_health_score(jobs, endpoints, gaps),
        "revenue_blockers": revenue_blockers,
        "runtime_blockers": runtime_blockers,
        "recommendations": build_recommendations(gaps),
        "meta": {
            "redact_secrets": redact_secrets,
            "schema_version": "2026-02-18",
        },
    }
    return payload


def validate_snapshot(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_top = {
        "generated_at",
        "hosts",
        "runtimes",
        "jobs",
        "endpoints",
        "credentials",
        "pipelines",
        "revenue",
        "gaps",
        "health_score",
        "revenue_blockers",
        "runtime_blockers",
        "recommendations",
    }
    for k in required_top:
        if k not in data:
            errors.append(f"missing top-level key: {k}")

    jobs = data.get("jobs", [])
    if not isinstance(jobs, list):
        errors.append("jobs must be a list")
        return errors

    required_job = {
        "label",
        "source_plist",
        "loaded_state",
        "last_exit_code",
        "program",
        "stdout_path",
        "stderr_path",
        "exists_flags",
        "function_group",
        "canonical",
        "disabled_reason",
        "depends_on_endpoints",
        "window_policy",
    }
    for idx, job in enumerate(jobs):
        if not isinstance(job, dict):
            errors.append(f"jobs[{idx}] is not an object")
            continue
        missing = sorted(required_job - set(job.keys()))
        if missing:
            errors.append(f"jobs[{idx}] missing fields: {', '.join(missing)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit AI Empire infrastructure/runtime")
    parser.add_argument("--mode", choices=["snapshot", "verify"], default="snapshot")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--redact-secrets", default="true", choices=["true", "false"])
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()
    redact = parse_bool(args.redact_secrets)

    if args.mode == "snapshot":
        data = collect_snapshot(redact_secrets=redact)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[audit] snapshot written: {output_path}")
        print(f"[audit] jobs={len(data.get('jobs', []))} gaps={len(data.get('gaps', []))}")
        return 0

    if output_path.exists():
        try:
            data = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"[audit] failed to parse {output_path}: {exc}")
            return 1
    else:
        data = collect_snapshot(redact_secrets=redact)

    errors = validate_snapshot(data)
    if errors:
        print("[audit] verify FAILED")
        for e in errors:
            print(f"- {e}")
        return 1

    print("[audit] verify OK")
    print(f"[audit] jobs={len(data.get('jobs', []))} gaps={len(data.get('gaps', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
