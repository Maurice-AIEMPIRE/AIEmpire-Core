from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE_PATH = ROOT / "automation" / "config" / "jarvis_profile.json"


def default_profile() -> Dict[str, Any]:
    return {
        "profile_name": "jarvis",
        "wake_word": "jarvis",
        "language": "de-DE",
        "audio": {
            "preferred_input_contains": ["DJI", "Wireless Mic", "Mikrofon"],
            "preferred_output_contains": ["AirPods", "Lautsprecher", "Speaker"],
            "strict_input": False,
            "strict_output": False,
        },
        "assistant": {
            "provider": "ollama",
            "model": "llama3.1:8b",
            "ollama_url": "http://127.0.0.1:11434",
            "system_prompt": (
                "Du bist Jarvis fuer Maurice. Antworte knapp, direkt, umsetzbar. "
                "Bei operativen Befehlen gib zuerst das Ergebnis, dann maximal 3 naechste Schritte."
            ),
        },
        "tts": {
            "enabled": True,
            "voice": "Anna",
            "rate": 190,
            "max_chars": 320,
        },
        "routing": {
            "default_agents": 6,
            "default_task_type": "strategy",
            "allow_shell_commands": False,
        },
        "security": {
            "api_token": "",
        },
    }


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def ensure_profile_exists(path: Path) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = default_profile()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_profile(path: Path) -> Dict[str, Any]:
    base = default_profile()
    if not path.exists():
        return base
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return base
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid profile JSON at {path}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit(f"Profile must be a JSON object: {path}")
    return _deep_merge(base, parsed)


def _safe_int(value: str) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def list_audio_devices() -> Dict[str, Any]:
    cmd = ["system_profiler", "SPAudioDataType"]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        return {
            "ok": False,
            "error": process.stderr.strip() or "system_profiler failed",
            "devices": [],
            "defaults": {"input": "", "output": ""},
        }

    devices: Dict[str, Dict[str, Any]] = {}
    current_name = ""

    for line in process.stdout.splitlines():
        name_match = re.match(r"^\s{8}(.+):\s*$", line)
        if name_match:
            maybe_name = name_match.group(1).strip()
            if maybe_name.lower() == "devices":
                continue
            current_name = maybe_name
            if current_name not in devices:
                devices[current_name] = {
                    "name": current_name,
                    "default_input": False,
                    "default_output": False,
                    "input_channels": 0,
                    "output_channels": 0,
                    "transport": "",
                }
            continue

        prop_match = re.match(r"^\s{10,}([^:]+):\s*(.*)$", line)
        if not prop_match or not current_name:
            continue

        key = prop_match.group(1).strip()
        value = prop_match.group(2).strip()
        item = devices[current_name]

        if key == "Default Input Device" and value.lower() == "yes":
            item["default_input"] = True
        elif key in {"Default Output Device", "Default System Output Device"} and value.lower() == "yes":
            item["default_output"] = True
        elif key == "Input Channels":
            item["input_channels"] = _safe_int(value)
        elif key == "Output Channels":
            item["output_channels"] = _safe_int(value)
        elif key == "Transport":
            item["transport"] = value

    device_list = list(devices.values())
    default_input = ""
    default_output = ""
    for device in device_list:
        if device.get("default_input"):
            default_input = str(device.get("name", ""))
        if device.get("default_output"):
            default_output = str(device.get("name", ""))

    return {
        "ok": True,
        "devices": device_list,
        "defaults": {
            "input": default_input,
            "output": default_output,
        },
    }


def _preferred_device(
    devices: List[Dict[str, Any]], patterns: List[str], role: str
) -> Optional[Dict[str, Any]]:
    if not patterns:
        return None
    lowered_patterns = [str(p).lower() for p in patterns if str(p).strip()]
    if not lowered_patterns:
        return None

    role_key = "input_channels" if role == "input" else "output_channels"
    for pattern in lowered_patterns:
        for device in devices:
            channels = int(device.get(role_key, 0) or 0)
            if channels <= 0:
                continue
            name = str(device.get("name", ""))
            if pattern in name.lower():
                return device
    return None


def build_audio_doctor_report(profile: Dict[str, Any]) -> Dict[str, Any]:
    data = list_audio_devices()
    if not data.get("ok"):
        return {
            "ok": False,
            "error": data.get("error", "audio detection failed"),
            "defaults": {"input": "", "output": ""},
            "preferred": {"input": "", "output": ""},
            "input_ok": False,
            "output_ok": False,
            "devices": [],
            "notes": ["Audio detection failed. Check macOS permissions and hardware."],
        }

    devices = data.get("devices", [])
    defaults = data.get("defaults", {})
    audio_cfg = profile.get("audio", {}) if isinstance(profile.get("audio"), dict) else {}

    pref_input = _preferred_device(
        devices,
        list(audio_cfg.get("preferred_input_contains", []) or []),
        role="input",
    )
    pref_output = _preferred_device(
        devices,
        list(audio_cfg.get("preferred_output_contains", []) or []),
        role="output",
    )

    default_input = str(defaults.get("input", ""))
    default_output = str(defaults.get("output", ""))
    preferred_input_name = str(pref_input.get("name", "")) if pref_input else ""
    preferred_output_name = str(pref_output.get("name", "")) if pref_output else ""

    input_ok = True
    output_ok = True
    notes: List[str] = []

    if preferred_input_name:
        input_ok = default_input == preferred_input_name
        if not input_ok:
            notes.append(
                f"Default input is '{default_input or 'none'}', preferred is '{preferred_input_name}'."
            )
    else:
        notes.append("No preferred input device match found in profile patterns.")

    if preferred_output_name:
        output_ok = default_output == preferred_output_name
        if not output_ok:
            notes.append(
                f"Default output is '{default_output or 'none'}', preferred is '{preferred_output_name}'."
            )
    else:
        notes.append("No preferred output device match found in profile patterns.")

    if not default_input:
        input_ok = False
        notes.append("No default input device detected.")
    if not default_output:
        output_ok = False
        notes.append("No default output device detected.")

    return {
        "ok": True,
        "defaults": {"input": default_input, "output": default_output},
        "preferred": {"input": preferred_input_name, "output": preferred_output_name},
        "input_ok": input_ok,
        "output_ok": output_ok,
        "devices": devices,
        "notes": notes,
    }


def _switch_audio_device(kind: str, target_name: str) -> Dict[str, Any]:
    binary = shutil.which("SwitchAudioSource")
    if not binary:
        return {
            "ok": False,
            "error": "SwitchAudioSource not installed. Install with: brew install switchaudio-osx",
        }

    cmd = [binary, "-t", kind, "-s", target_name]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        return {
            "ok": False,
            "error": process.stderr.strip() or process.stdout.strip() or "device switch failed",
        }
    return {"ok": True, "command": cmd}


def apply_audio_profile(profile: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    before = build_audio_doctor_report(profile)
    actions: List[Dict[str, Any]] = []

    if not before.get("ok"):
        return {
            "ok": False,
            "error": before.get("error", "audio check failed"),
            "before": before,
            "after": before,
            "actions": actions,
        }

    default_input = str(before.get("defaults", {}).get("input", ""))
    default_output = str(before.get("defaults", {}).get("output", ""))
    preferred_input = str(before.get("preferred", {}).get("input", ""))
    preferred_output = str(before.get("preferred", {}).get("output", ""))

    if preferred_input and preferred_input != default_input:
        if dry_run:
            actions.append({"kind": "input", "target": preferred_input, "ok": True, "dry_run": True})
        else:
            result = _switch_audio_device("input", preferred_input)
            actions.append({"kind": "input", "target": preferred_input, **result})

    if preferred_output and preferred_output != default_output:
        if dry_run:
            actions.append({"kind": "output", "target": preferred_output, "ok": True, "dry_run": True})
        else:
            result = _switch_audio_device("output", preferred_output)
            actions.append({"kind": "output", "target": preferred_output, **result})

    after = build_audio_doctor_report(profile)
    all_ok = all(bool(item.get("ok")) for item in actions) if actions else True

    return {
        "ok": all_ok and bool(after.get("ok")),
        "before": before,
        "after": after,
        "actions": actions,
    }


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, X-Jarvis-Token")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _run_subprocess(command: List[str], timeout: int = 300) -> Dict[str, Any]:
    try:
        process = subprocess.run(
            command,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit_code": -1, "stdout": "", "stderr": "command timeout"}

    return {
        "ok": process.returncode == 0,
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def _summarize_process_result(result: Dict[str, Any], max_chars: int = 1800) -> str:
    if result.get("ok"):
        text = str(result.get("stdout", "")).strip()
        if not text:
            text = "Ausgefuehrt ohne Textausgabe."
    else:
        text = str(result.get("stderr", "")).strip() or str(result.get("stdout", "")).strip()
        if not text:
            text = "Ausfuehrung fehlgeschlagen."
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n..."
    return text


def _ollama_request(base_url: str, payload: Dict[str, Any], timeout: int = 180) -> Dict[str, Any]:
    endpoint = base_url.rstrip("/") + "/api/generate"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            return {"response": str(parsed)}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama connection error: {exc}") from exc


def _normalize_command(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _extract_workflow(lower_command: str) -> Optional[str]:
    aliases = {
        "threads": "threads",
        "thread": "threads",
        "tweets": "tweets",
        "tweet": "tweets",
        "prompts": "prompts",
        "prompt": "prompts",
        "monetization": "monetization",
        "monetarisierung": "monetization",
        "full": "full",
        "komplett": "full",
        "alles": "full",
    }

    tokens = lower_command.split()
    for token in tokens:
        if token in aliases:
            return aliases[token]
    return None


def _shell_command(command: str) -> Dict[str, Any]:
    try:
        process = subprocess.run(
            command,
            cwd=str(ROOT),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit_code": -1, "stdout": "", "stderr": "shell timeout"}

    return {
        "ok": process.returncode == 0,
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def speak_text(text: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    tts_cfg = profile.get("tts", {}) if isinstance(profile.get("tts"), dict) else {}
    if not bool(tts_cfg.get("enabled", True)):
        return {"ok": True, "skipped": True, "reason": "tts disabled"}

    if not shutil.which("say"):
        return {"ok": False, "error": "say command not found"}

    message = _normalize_command(text)
    if not message:
        return {"ok": True, "skipped": True, "reason": "empty message"}

    max_chars = int(tts_cfg.get("max_chars", 320) or 320)
    if len(message) > max_chars:
        message = message[:max_chars].rstrip() + " ..."

    voice = str(tts_cfg.get("voice", "")).strip()
    rate = int(tts_cfg.get("rate", 190) or 190)

    cmd = ["say", "-r", str(rate)]
    if voice:
        cmd.extend(["-v", voice])
    cmd.append(message)

    try:
        subprocess.Popen(cmd, cwd=str(ROOT))
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    return {"ok": True}


def _help_text() -> str:
    return (
        "Befehle: status, plan, workflow <threads|tweets|prompts|monetization|full>, "
        "multi <frage>, audio check, audio fix, help. "
        "Alles andere geht als freie Frage an Ollama."
    )


def dispatch_command(command: str, profile: Dict[str, Any], execute: bool = False) -> Dict[str, Any]:
    normalized = _normalize_command(command)
    lower = normalized.lower()

    if not normalized:
        return {"ok": False, "action": "empty", "reply": "Kein Befehl erkannt."}

    if lower in {"help", "hilfe", "commands", "befehle"}:
        return {"ok": True, "action": "help", "reply": _help_text()}

    if lower.startswith("audio check") or lower == "audio":
        report = build_audio_doctor_report(profile)
        if not report.get("ok"):
            return {
                "ok": False,
                "action": "audio-check",
                "reply": f"Audio-Check fehlgeschlagen: {report.get('error', 'unknown')}",
                "data": report,
            }
        defaults = report.get("defaults", {})
        preferred = report.get("preferred", {})
        reply = (
            f"Input default: {defaults.get('input') or 'none'} | bevorzugt: {preferred.get('input') or 'none'}\n"
            f"Output default: {defaults.get('output') or 'none'} | bevorzugt: {preferred.get('output') or 'none'}\n"
            f"Input OK: {report.get('input_ok')} | Output OK: {report.get('output_ok')}"
        )
        return {"ok": True, "action": "audio-check", "reply": reply, "data": report}

    if lower.startswith("audio fix"):
        applied = apply_audio_profile(profile, dry_run=False)
        if not applied.get("ok"):
            reply = "Audio-Fix nicht vollstaendig erfolgreich."
        else:
            reply = "Audio-Profil angewendet."
        return {"ok": bool(applied.get("ok")), "action": "audio-fix", "reply": reply, "data": applied}

    if lower.startswith("status") or lower.startswith("lage"):
        result = _run_subprocess([sys.executable, "-m", "automation.mission_control", "status"])
        reply = _summarize_process_result(result)
        return {"ok": bool(result.get("ok")), "action": "status", "reply": reply, "data": result}

    if lower.startswith("plan") or "sprint" in lower:
        result = _run_subprocess([sys.executable, "-m", "automation.mission_control", "plan"])
        reply = _summarize_process_result(result)
        return {"ok": bool(result.get("ok")), "action": "plan", "reply": reply, "data": result}

    if lower.startswith("workflow") or lower.startswith("run"):
        workflow = _extract_workflow(lower) or "full"
        cmd = [sys.executable, "-m", "automation", "run", "--workflow", workflow]
        if execute:
            cmd.append("--execute")
        result = _run_subprocess(cmd)
        reply = _summarize_process_result(result)
        return {
            "ok": bool(result.get("ok")),
            "action": "workflow",
            "workflow": workflow,
            "reply": reply,
            "data": result,
        }

    if lower.startswith("multi") or lower.startswith("parallel"):
        prompt = normalized
        prompt = re.sub(r"^(multi|parallel)\s*", "", prompt, flags=re.IGNORECASE).strip() or normalized
        routing = profile.get("routing", {}) if isinstance(profile.get("routing"), dict) else {}
        agents = int(routing.get("default_agents", 6) or 6)
        task_type = str(routing.get("default_task_type", "strategy") or "strategy")
        cmd = [
            sys.executable,
            "-m",
            "automation.mission_control",
            "multi-chat",
            "--prompt",
            prompt,
            "--agents",
            str(agents),
            "--task-type",
            task_type,
            "--diversify",
        ]
        if execute:
            cmd.append("--execute")
        result = _run_subprocess(cmd, timeout=900)
        reply = _summarize_process_result(result)
        return {"ok": bool(result.get("ok")), "action": "multi-chat", "reply": reply, "data": result}

    if lower.startswith("shell "):
        routing = profile.get("routing", {}) if isinstance(profile.get("routing"), dict) else {}
        if not bool(routing.get("allow_shell_commands", False)):
            return {
                "ok": False,
                "action": "shell",
                "reply": "Shell-Befehle sind im Profil deaktiviert (routing.allow_shell_commands=false).",
            }
        shell_text = normalized[6:].strip()
        result = _shell_command(shell_text)
        reply = _summarize_process_result(result)
        return {"ok": bool(result.get("ok")), "action": "shell", "reply": reply, "data": result}

    assistant = profile.get("assistant", {}) if isinstance(profile.get("assistant"), dict) else {}
    provider = str(assistant.get("provider", "ollama")).lower()
    if provider != "ollama":
        return {
            "ok": False,
            "action": "qa",
            "reply": "Nur provider=ollama wird aktuell unterstuetzt.",
        }

    model = str(assistant.get("model", "llama3.1:8b"))
    ollama_url = str(assistant.get("ollama_url", "http://127.0.0.1:11434"))
    system_prompt = str(assistant.get("system_prompt", "")).strip()
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": normalized,
        "stream": False,
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        raw = _ollama_request(ollama_url, payload)
        reply = str(raw.get("response", "")).strip() or "Keine Antwort vom Modell."
        return {
            "ok": True,
            "action": "qa",
            "reply": reply,
            "data": {"provider": "ollama", "model": model, "raw": raw},
        }
    except Exception as exc:
        return {
            "ok": False,
            "action": "qa",
            "reply": f"Ollama-Fehler: {exc}",
        }


HTML_TEMPLATE = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Jarvis Voice Control</title>
  <style>
    :root {
      --bg: #08131f;
      --panel: #102437;
      --ink: #edf7ff;
      --muted: #9ab1c6;
      --accent: #2ed3a5;
      --danger: #ff6d6d;
      --warn: #f1c15b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background:
        radial-gradient(1000px 500px at 10% -10%, rgba(46, 211, 165, 0.2), transparent 60%),
        radial-gradient(900px 500px at 90% 0%, rgba(71, 132, 255, 0.18), transparent 60%),
        var(--bg);
      color: var(--ink);
      min-height: 100vh;
      padding: 16px;
      display: grid;
      place-items: center;
    }
    .app {
      width: min(980px, 100%);
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.14);
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
      box-shadow: 0 30px 80px rgba(0,0,0,0.35);
      overflow: hidden;
    }
    .head {
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.14);
      display: flex;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;
      align-items: center;
      background: rgba(0,0,0,0.25);
    }
    .brand {
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .meta {
      color: var(--muted);
      font-size: 13px;
    }
    .meta strong { color: var(--ink); }
    .status {
      font-size: 12px;
      color: var(--muted);
    }
    .status.ok { color: var(--accent); }
    .status.err { color: var(--danger); }
    .chat {
      min-height: 52vh;
      max-height: 62vh;
      overflow: auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      background: rgba(0,0,0,0.14);
    }
    .msg {
      max-width: 92%;
      border-radius: 12px;
      padding: 10px 12px;
      line-height: 1.5;
      white-space: pre-wrap;
      font-size: 15px;
      border: 1px solid transparent;
    }
    .heard {
      margin-right: auto;
      background: rgba(255,255,255,0.06);
      border-color: rgba(255,255,255,0.1);
      color: var(--muted);
      font-size: 13px;
    }
    .user {
      margin-left: auto;
      background: #225db3;
    }
    .assistant {
      margin-right: auto;
      background: #1a334e;
      border-color: rgba(255,255,255,0.1);
    }
    .controls {
      padding: 14px;
      border-top: 1px solid rgba(255,255,255,0.14);
      display: grid;
      grid-template-columns: 1fr auto auto auto;
      gap: 10px;
      align-items: stretch;
    }
    textarea {
      width: 100%;
      resize: vertical;
      min-height: 56px;
      max-height: 180px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.18);
      background: #0e1d2f;
      color: var(--ink);
      padding: 10px 12px;
      font-size: 15px;
    }
    button {
      border: 0;
      border-radius: 10px;
      min-height: 44px;
      padding: 0 14px;
      cursor: pointer;
      font-weight: 700;
      font-size: 14px;
      background: var(--accent);
      color: #05261f;
    }
    button.secondary {
      background: #314f74;
      color: #fff;
    }
    button.warn {
      background: var(--warn);
      color: #2c1f00;
    }
    button.danger {
      background: var(--danger);
      color: #300;
    }
    .toolbar {
      padding: 0 14px 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
    }
    .chip {
      border: 1px solid rgba(255,255,255,0.16);
      border-radius: 999px;
      padding: 4px 10px;
      background: rgba(255,255,255,0.03);
    }
    input[type="password"] {
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.18);
      background: #0e1d2f;
      color: var(--ink);
      min-height: 34px;
      padding: 6px 8px;
      width: min(260px, 100%);
    }
    @media (max-width: 900px) {
      .controls {
        grid-template-columns: 1fr 1fr;
      }
      textarea {
        grid-column: 1 / -1;
      }
    }
    @media (max-width: 620px) {
      .controls {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="app">
    <header class="head">
      <div>
        <div class="brand">Jarvis Profile</div>
        <div class="meta">Wake-Word: <strong id="wakeWordLabel"></strong> | Model: <strong id="modelLabel"></strong></div>
      </div>
      <div id="status" class="status">Starte...</div>
    </header>

    <section id="chat" class="chat"></section>

    <section class="controls">
      <textarea id="prompt" placeholder="Textbefehl (oder sprich: 'Jarvis ...')"></textarea>
      <button id="micBtn" class="secondary" type="button">Mic Start</button>
      <button id="sendBtn" type="button">Senden</button>
      <button id="audioBtn" class="warn" type="button">Audio Check</button>
    </section>

    <section class="toolbar">
      <span class="chip" id="listenState">Mic: aus</span>
      <span class="chip" id="wakeState">Wake: wartend</span>
      <label class="chip"><input type="checkbox" id="speakToggle" checked /> Antwort sprechen</label>
      <label class="chip" id="tokenWrap">Token: <input type="password" id="tokenInput" placeholder="optional" /></label>
    </section>
  </main>

  <script>
    const WAKE_WORD = __WAKE_WORD__;
    const MODEL_NAME = __MODEL_NAME__;
    const LANGUAGE = __LANGUAGE__;
    const TOKEN_REQUIRED = __TOKEN_REQUIRED__;

    const chatEl = document.getElementById("chat");
    const statusEl = document.getElementById("status");
    const promptEl = document.getElementById("prompt");
    const micBtn = document.getElementById("micBtn");
    const sendBtn = document.getElementById("sendBtn");
    const audioBtn = document.getElementById("audioBtn");
    const listenState = document.getElementById("listenState");
    const wakeState = document.getElementById("wakeState");
    const wakeWordLabel = document.getElementById("wakeWordLabel");
    const modelLabel = document.getElementById("modelLabel");
    const speakToggle = document.getElementById("speakToggle");
    const tokenWrap = document.getElementById("tokenWrap");
    const tokenInput = document.getElementById("tokenInput");

    wakeWordLabel.textContent = WAKE_WORD;
    modelLabel.textContent = MODEL_NAME;

    if (!TOKEN_REQUIRED) {
      tokenWrap.style.display = "none";
    }

    const urlToken = new URLSearchParams(window.location.search).get("token") || "";
    tokenInput.value = urlToken;

    function append(role, text) {
      const node = document.createElement("div");
      node.className = "msg " + role;
      node.textContent = text;
      chatEl.appendChild(node);
      chatEl.scrollTop = chatEl.scrollHeight;
    }

    function setStatus(msg, kind = "") {
      statusEl.textContent = msg;
      statusEl.className = "status" + (kind ? " " + kind : "");
    }

    function speakBrowser(text) {
      if (!speakToggle.checked) return;
      if (!("speechSynthesis" in window)) return;
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = LANGUAGE;
      speechSynthesis.cancel();
      speechSynthesis.speak(utter);
    }

    function commandFromTranscript(transcript) {
      const lower = transcript.toLowerCase();
      const wakeLower = WAKE_WORD.toLowerCase();
      const idx = lower.indexOf(wakeLower);
      if (idx === -1) return null;
      let cmd = transcript.slice(idx + WAKE_WORD.length).trim();
      cmd = cmd.replace(/^[,.:;\-]+/, "").trim();
      return cmd;
    }

    async function apiPost(path, payload) {
      const token = (tokenInput.value || "").trim();
      const headers = { "Content-Type": "application/json" };
      if (token) headers["X-Jarvis-Token"] = token;
      const res = await fetch(path, {
        method: "POST",
        headers,
        body: JSON.stringify({ ...payload, token }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || data.reply || ("HTTP " + res.status));
      return data;
    }

    async function sendCommand(command, rawText = "") {
      const clean = (command || "").trim();
      if (!clean) return;
      append("user", clean);
      sendBtn.disabled = true;
      try {
        const data = await apiPost("/api/command", {
          command: clean,
          raw: rawText || clean,
          source: "web",
        });
        const reply = data.reply || "(leer)";
        append("assistant", reply);
        speakBrowser(reply);
      } catch (err) {
        append("assistant", "Fehler: " + err.message);
      } finally {
        sendBtn.disabled = false;
      }
    }

    sendBtn.addEventListener("click", () => {
      const text = promptEl.value.trim();
      promptEl.value = "";
      sendCommand(text, text);
    });

    promptEl.addEventListener("keydown", (ev) => {
      if ((ev.metaKey || ev.ctrlKey) && ev.key === "Enter") {
        const text = promptEl.value.trim();
        promptEl.value = "";
        sendCommand(text, text);
      }
    });

    audioBtn.addEventListener("click", async () => {
      try {
        const data = await apiPost("/api/audio", { dry_run: true });
        const a = data.audio || {};
        const msg =
          "Input default: " + (a.defaults?.input || "none") + " | bevorzugt: " + (a.preferred?.input || "none") + "\n" +
          "Output default: " + (a.defaults?.output || "none") + " | bevorzugt: " + (a.preferred?.output || "none") + "\n" +
          "Input OK: " + a.input_ok + " | Output OK: " + a.output_ok;
        append("assistant", msg);
      } catch (err) {
        append("assistant", "Audio Check Fehler: " + err.message);
      }
    });

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let listening = false;

    function setListening(next) {
      listening = next;
      listenState.textContent = "Mic: " + (listening ? "an" : "aus");
      wakeState.textContent = "Wake: " + (listening ? "wartend" : "inaktiv");
      micBtn.textContent = listening ? "Mic Stop" : "Mic Start";
      micBtn.className = listening ? "danger" : "secondary";
    }

    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.lang = LANGUAGE;
      recognition.interimResults = false;
      recognition.continuous = true;

      recognition.onresult = (event) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (!result.isFinal) continue;
          const transcript = (result[0]?.transcript || "").trim();
          if (!transcript) continue;
          append("heard", "Gehort: " + transcript);

          const cmd = commandFromTranscript(transcript);
          if (cmd === null) continue;

          if (!cmd) {
            wakeState.textContent = "Wake: erkannt";
            append("assistant", "Ja?");
            speakBrowser("Ja?");
            continue;
          }

          wakeState.textContent = "Wake: erkannt";
          sendCommand(cmd, transcript);
          setTimeout(() => {
            if (listening) wakeState.textContent = "Wake: wartend";
          }, 1200);
        }
      };

      recognition.onerror = (event) => {
        append("assistant", "Speech Error: " + event.error);
      };

      recognition.onend = () => {
        if (listening) {
          try { recognition.start(); } catch (_) {}
        }
      };
    } else {
      micBtn.disabled = true;
      micBtn.textContent = "Mic nicht verfuegbar";
      append("assistant", "SpeechRecognition wird in diesem Browser nicht unterstuetzt.");
    }

    micBtn.addEventListener("click", () => {
      if (!recognition) return;
      if (!listening) {
        try {
          recognition.start();
          setListening(true);
        } catch (err) {
          append("assistant", "Mic Start Fehler: " + err.message);
        }
      } else {
        listening = false;
        try { recognition.stop(); } catch (_) {}
        setListening(false);
      }
    });

    async function boot() {
      try {
        const res = await fetch("/api/health");
        const data = await res.json();
        if (data.ok) {
          setStatus("Jarvis online", "ok");
          append("assistant", "Jarvis bereit. Sag: '" + WAKE_WORD + " status' oder '" + WAKE_WORD + " help'.");
        } else {
          setStatus("Health-Check fehlgeschlagen", "err");
        }
      } catch (err) {
        setStatus("Backend nicht erreichbar", "err");
      }
    }

    boot();
  </script>
</body>
</html>
"""


class JarvisRuntime:
    def __init__(self, profile_path: Path, execute: bool = False, no_tts: bool = False, token_override: Optional[str] = None):
        self.profile_path = profile_path
        self.profile = load_profile(profile_path)
        self.execute = execute
        self.no_tts = no_tts
        self.last_audio_report: Dict[str, Any] = {}
        self.last_audio_report_at = 0.0

        if token_override is not None:
            security = self.profile.setdefault("security", {})
            if isinstance(security, dict):
                security["api_token"] = token_override

    def _token_required(self) -> str:
        security = self.profile.get("security", {}) if isinstance(self.profile.get("security"), dict) else {}
        return str(security.get("api_token", "") or "").strip()

    def check_token(self, token: str) -> bool:
        required = self._token_required()
        if not required:
            return True
        return token == required

    def health(self) -> Dict[str, Any]:
        assistant = self.profile.get("assistant", {}) if isinstance(self.profile.get("assistant"), dict) else {}
        return {
            "ok": True,
            "profile": str(self.profile_path),
            "profile_name": self.profile.get("profile_name", "jarvis"),
            "wake_word": self.profile.get("wake_word", "jarvis"),
            "language": self.profile.get("language", "de-DE"),
            "execute": self.execute,
            "token_required": bool(self._token_required()),
            "assistant_provider": assistant.get("provider", "ollama"),
            "assistant_model": assistant.get("model", "llama3.1:8b"),
            "time_unix": int(time.time()),
        }

    def audio_report(self, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force and self.last_audio_report and now - self.last_audio_report_at < 20:
            return self.last_audio_report
        report = build_audio_doctor_report(self.profile)
        self.last_audio_report = report
        self.last_audio_report_at = now
        return report

    def handle_command(self, command: str, source: str = "api") -> Dict[str, Any]:
        result = dispatch_command(command=command, profile=self.profile, execute=self.execute)
        reply = str(result.get("reply", "")).strip()

        tts_result = {"ok": True, "skipped": True, "reason": "no text"}
        if reply and not self.no_tts and source != "web-mobile-only":
            tts_result = speak_text(reply, self.profile)
        result["tts"] = tts_result
        return result

    def render_html(self) -> str:
        assistant = self.profile.get("assistant", {}) if isinstance(self.profile.get("assistant"), dict) else {}
        html = HTML_TEMPLATE
        html = html.replace("__WAKE_WORD__", json.dumps(str(self.profile.get("wake_word", "jarvis")), ensure_ascii=False))
        html = html.replace("__MODEL_NAME__", json.dumps(str(assistant.get("model", "llama3.1:8b")), ensure_ascii=False))
        html = html.replace("__LANGUAGE__", json.dumps(str(self.profile.get("language", "de-DE")), ensure_ascii=False))
        html = html.replace("__TOKEN_REQUIRED__", "true" if bool(self._token_required()) else "false")
        return html


def build_handler(runtime: JarvisRuntime) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "Jarvis/1.0"

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Jarvis-Token")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path in {"/", "/index.html"}:
                html = runtime.render_html().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
                return

            if parsed.path == "/api/health":
                _json_response(self, 200, runtime.health())
                return

            _json_response(self, 404, {"ok": False, "error": "not found"})

        def do_POST(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            data = _read_json(self)
            token = str(self.headers.get("X-Jarvis-Token", "") or data.get("token", "")).strip()

            if not runtime.check_token(token):
                _json_response(self, 401, {"ok": False, "error": "invalid token", "reply": "Unauthorized"})
                return

            if parsed.path == "/api/command":
                command = str(data.get("command", "") or "").strip()
                if not command:
                    _json_response(self, 400, {"ok": False, "error": "command is required"})
                    return
                source = str(data.get("source", "api") or "api")
                result = runtime.handle_command(command=command, source=source)
                payload = {"ok": bool(result.get("ok")), **result}
                _json_response(self, 200 if payload.get("ok") else 400, payload)
                return

            if parsed.path == "/api/audio":
                dry_run = bool(data.get("dry_run", True))
                if dry_run:
                    report = runtime.audio_report(force=True)
                    _json_response(self, 200, {"ok": bool(report.get("ok")), "audio": report})
                    return
                applied = apply_audio_profile(runtime.profile, dry_run=False)
                runtime.audio_report(force=True)
                _json_response(self, 200 if applied.get("ok") else 400, {"ok": bool(applied.get("ok")), "audio": applied})
                return

            _json_response(self, 404, {"ok": False, "error": "not found"})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def _public_urls(host: str, port: int) -> List[str]:
    urls = [f"http://{host}:{port}"]
    if host in {"0.0.0.0", "::"}:
        try:
            lan_ip = socket.gethostbyname(socket.gethostname())
            if lan_ip and lan_ip not in {"127.0.0.1", "0.0.0.0"}:
                urls.append(f"http://{lan_ip}:{port}")
        except Exception:
            pass
    return urls


def cmd_init_profile(args: argparse.Namespace) -> int:
    path = Path(args.profile).expanduser().resolve()
    if path.exists() and not args.force:
        print(f"Profile exists: {path}")
        return 0
    ensure_profile_exists(path)
    print(f"Profile written: {path}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    profile_path = Path(args.profile).expanduser().resolve()
    profile = load_profile(profile_path)
    report = build_audio_doctor_report(profile)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


def cmd_audio_apply(args: argparse.Namespace) -> int:
    profile_path = Path(args.profile).expanduser().resolve()
    profile = load_profile(profile_path)
    result = apply_audio_profile(profile, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def cmd_run(args: argparse.Namespace) -> int:
    profile_path = Path(args.profile).expanduser().resolve()
    runtime = JarvisRuntime(
        profile_path=profile_path,
        execute=args.execute,
        no_tts=args.no_tts,
        token_override=args.token,
    )
    result = runtime.handle_command(command=args.command, source="cli")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def cmd_serve(args: argparse.Namespace) -> int:
    profile_path = Path(args.profile).expanduser().resolve()
    runtime = JarvisRuntime(
        profile_path=profile_path,
        execute=args.execute,
        no_tts=args.no_tts,
        token_override=args.token,
    )

    handler = build_handler(runtime)
    server = ThreadingHTTPServer((args.host, args.port), handler)

    info = runtime.health()
    info["urls"] = _public_urls(args.host, args.port)
    print(json.dumps(info, ensure_ascii=False, indent=2))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jarvis voice profile: wake-word web control + automation routing")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE_PATH), help="Path to jarvis profile JSON")

    sub = parser.add_subparsers(dest="command_name", required=True)

    p_init = sub.add_parser("init-profile", help="Write default jarvis profile if missing")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing profile")
    p_init.set_defaults(func=cmd_init_profile)

    p_doctor = sub.add_parser("doctor", help="Inspect current audio devices vs preferred profile")
    p_doctor.set_defaults(func=cmd_doctor)

    p_apply = sub.add_parser("audio-apply", help="Apply preferred audio devices (requires SwitchAudioSource)")
    p_apply.add_argument("--dry-run", action="store_true", help="Only show planned actions")
    p_apply.set_defaults(func=cmd_audio_apply)

    p_run = sub.add_parser("run", help="Execute a single jarvis command")
    p_run.add_argument("command", help="Command text")
    p_run.add_argument("--execute", action="store_true", help="Execute workflows with real API calls")
    p_run.add_argument("--no-tts", action="store_true", help="Disable local say() voice output")
    p_run.add_argument("--token", default=None, help="Override API token in memory")
    p_run.set_defaults(func=cmd_run)

    p_serve = sub.add_parser("serve", help="Start Jarvis web server with wake-word support")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8877)
    p_serve.add_argument("--execute", action="store_true", help="Execute workflows with real API calls")
    p_serve.add_argument("--no-tts", action="store_true", help="Disable local say() voice output")
    p_serve.add_argument("--token", default=None, help="Override API token in memory")
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
