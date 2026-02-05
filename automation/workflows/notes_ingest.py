from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from automation.utils.files import ensure_dir, read_text, timestamp_id, write_json, write_text

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INTAKE_DIR = ROOT / "claude_intake"
PROMPTS_DIR = ROOT / "automation" / "prompts"


@dataclass
class Note:
    note_id: str
    title: str
    modified: str
    body: str
    source: str


def _run_osascript(script: str, args: List[str]) -> str:
    cmd = ["osascript", "-e", script, *args]
    return subprocess.check_output(cmd, text=True)


def _html_to_text(raw: str) -> str:
    if not raw:
        return ""
    text = raw
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"</(div|p|li|h[1-6]|tr|table)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def export_notes_applescript(limit: int = 0, since_days: int = 0) -> List[Note]:
    script = r'''
    on run argv
        set limitNotes to 0
        set sinceDays to 0
        if (count of argv) > 0 then set limitNotes to item 1 of argv as integer
        if (count of argv) > 1 then set sinceDays to item 2 of argv as integer
        set cutoff to (current date) - (sinceDays * days)
        set outLines to {}
        tell application "Notes"
            set allNotes to every note
            set counter to 0
            repeat with n in allNotes
                set m to modification date of n
                if (sinceDays is 0) or (m is greater than cutoff) then
                    set noteBody to body of n
                    set body64 to do shell script "python3 -c 'import base64,sys;print(base64.b64encode(sys.stdin.buffer.read()).decode())'" input noteBody
                    set line to (id of n as string) & "\t" & (name of n as string) & "\t" & (m as string) & "\t" & body64
                    set outLines to outLines & {line}
                    set counter to counter + 1
                    if (limitNotes > 0) and (counter >= limitNotes) then exit repeat
                end if
            end repeat
        end tell
        set AppleScript's text item delimiters to "\n"
        set output to outLines as string
        set AppleScript's text item delimiters to ""
        return output
    end run
    '''
    output = _run_osascript(script, [str(limit), str(since_days)])
    notes: List[Note] = []
    for line in output.splitlines():
        parts = line.split("\t", 3)
        if len(parts) != 4:
            continue
        note_id, title, modified, body64 = parts
        try:
            body_raw = base64.b64decode(body64.encode("utf-8")).decode("utf-8", errors="ignore")
        except Exception:
            body_raw = ""
        body = _html_to_text(body_raw)
        notes.append(Note(note_id=note_id, title=title.strip(), modified=modified.strip(), body=body, source="apple_notes"))
    return notes


def load_notes_from_folder(path: Path, limit: int = 0) -> List[Note]:
    SKIP_FILES = {"README.md", "INGESTED.md", "CLAUDE_HANDOFF.md"}
    files = sorted([p for p in path.glob("**/*") if p.suffix.lower() in {".md", ".txt"} and p.name not in SKIP_FILES])
    if limit > 0:
        files = files[:limit]
    notes: List[Note] = []
    for p in files:
        content = read_text(p)
        title = p.stem
        for line in content.splitlines():
            if line.strip().startswith("#"):
                title = line.strip().lstrip("#").strip()
                break
            if line.strip():
                break
        modified = dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        notes.append(Note(note_id=str(p), title=title, modified=modified, body=content.strip(), source="folder"))
    return notes


def truncate(text: str, max_chars: int) -> Tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars].rstrip() + "\n\n[TRUNCATED]", True


def render_prompt(template_path: Path, variables: Dict[str, str]) -> str:
    template = read_text(template_path)
    for key, value in variables.items():
        template = template.replace("{" + key + "}", value)
    return template


def parse_json_safe(text: str) -> Dict[str, object]:
    try:
        return json.loads(text)
    except Exception:
        # try to find JSON block in output
        match = re.search(r"\{.*\}\s*$", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {"raw": text}


def build_summary_markdown(run_id: str, results: List[Dict[str, object]]) -> str:
    nuggets: List[Dict[str, object]] = []
    for item in results:
        note_title = str(item.get("note_title", ""))
        note_date = str(item.get("note_date", ""))
        for nugget in item.get("nuggets", []) if isinstance(item.get("nuggets"), list) else []:
            if isinstance(nugget, dict):
                nugget_copy = dict(nugget)
                nugget_copy["note_title"] = note_title
                nugget_copy["note_date"] = note_date
                nuggets.append(nugget_copy)

    def score(n: Dict[str, object]) -> int:
        try:
            return int(n.get("score", 0))
        except Exception:
            return 0

    nuggets.sort(key=score, reverse=True)
    lines = [f"# Gold Nuggets Report ({run_id})", "", f"Gesamt-Nuggets: {len(nuggets)}", ""]

    lines.append("## Top Nuggets")
    for idx, nug in enumerate(nuggets[:25]):
        insight = str(nug.get("insight", ""))
        action = str(nug.get("action", ""))
        note_title = str(nug.get("note_title", ""))
        note_date = str(nug.get("note_date", ""))
        lines.append(f"{idx + 1}) {insight}")
        if action:
            lines.append(f"Action: {action}")
        if note_title or note_date:
            lines.append(f"Quelle: {note_title} ({note_date})")
        lines.append("")

    lines.append("## Nach Notiz")
    for item in results:
        title = str(item.get("note_title", ""))
        date = str(item.get("note_date", ""))
        summary = str(item.get("summary", ""))
        lines.append(f"### {title} ({date})")
        if summary:
            lines.append(summary)
        nuggets_list = item.get("nuggets", []) if isinstance(item.get("nuggets"), list) else []
        for nug in nuggets_list:
            if not isinstance(nug, dict):
                continue
            insight = str(nug.get("insight", ""))
            action = str(nug.get("action", ""))
            lines.append(f"- {insight}")
            if action:
                lines.append(f"Action: {action}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def save_raw_notes(notes: List[Note], run_dir: Path) -> None:
    ensure_dir(run_dir)
    data = [note.__dict__ for note in notes]
    write_json(run_dir / "notes_raw.json", {"notes": data})


def nugget_output_paths(run_id: str) -> Tuple[Path, Path]:
    nugget_dir = ROOT / "ai-vault" / "nuggets"
    ensure_dir(nugget_dir)
    json_path = nugget_dir / f"nuggets_{run_id}.json"
    md_path = nugget_dir / f"nuggets_{run_id}.md"
    return json_path, md_path


def ingest_notes(
    notes: List[Note],
    runner,
    nugget_count: int = 8,
    max_chars: int = 12000,
    run_id: Optional[str] = None,
) -> Tuple[str, str]:
    run_id = run_id or timestamp_id()
    run_dir = ROOT / "automation" / "runs" / f"ingest_{run_id}"
    ensure_dir(run_dir)
    save_raw_notes(notes, run_dir)

    template_path = PROMPTS_DIR / "nugget_extractor.md"
    results: List[Dict[str, object]] = []

    for note in notes:
        body, truncated = truncate(note.body, max_chars)
        variables = {
            "NOTE_TITLE": note.title,
            "NOTE_DATE": note.modified,
            "NOTE_BODY": body,
            "NUGGET_COUNT": str(nugget_count),
        }
        prompt = render_prompt(template_path, variables)
        result = runner.run_task("nugget_extraction", prompt)
        parsed = parse_json_safe(result.text)
        if isinstance(parsed, dict):
            parsed.setdefault("note_title", note.title)
            parsed.setdefault("note_date", note.modified)
            if truncated:
                parsed["truncated"] = True
        results.append(parsed)

    write_json(run_dir / "nuggets_raw.json", {"run_id": run_id, "results": results})
    summary_md = build_summary_markdown(run_id, results)
    write_text(run_dir / "nuggets_report.md", summary_md)

    json_path, md_path = nugget_output_paths(run_id)
    write_json(json_path, {"run_id": run_id, "results": results})
    write_text(md_path, summary_md)

    return str(json_path), str(md_path)
