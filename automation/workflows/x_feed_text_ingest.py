from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from automation.utils.files import ensure_dir, timestamp_id, write_json, write_text
from automation.workflows.notes_ingest import Note


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_X_FEED_DIR = ROOT / "claude_intake" / "x_feeds"
X_FEED_IMPORTS_DIR = ROOT / "external" / "imports" / "x_feed_text"

NOISE_PREFIXES = {
    "fragezeichen drücken",
    "tastatur kurzbefehle anzeigen",
    "youtube shorts",
    "youtube shorts automation",
    "top",
    "neueste",
    "personen",
    "medien",
    "listen",
    "neue posts sehen",
    "timeline durchsuchen",
    "suchfilter",
    "personen",
    "von jedem",
    "standort",
    "überall",
    "in deiner nähe",
    "erweiterte suche",
    "live auf x",
    "aktuelle trends",
    "was gibt’s neues?",
    "wem folgen?",
    "allgemeine geschäftsbedingungen",
    "datenschutzrichtlinien",
    "cookie-richtlinie",
    "barrierefreiheit",
    "anzeigen-info",
    "mehr anzeigen",
    "selbst mit grok erstellen",
    "©",
}


@dataclass
class XFeedRecord:
    post_id: str
    author: str
    created_at_raw: str
    content: str
    query: str
    source: str
    engagement_hints: str
    hash: str


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_line(line: str) -> str:
    return " ".join(str(line or "").replace("\r", " ").split()).strip()


def _is_noise(line: str) -> bool:
    low = line.lower().strip()
    if not low:
        return True
    if low in NOISE_PREFIXES:
        return True
    if any(low.startswith(prefix) for prefix in NOISE_PREFIXES):
        return True
    if re.fullmatch(r"\d+:\d+\s*/\s*\d+:\d+", low):
        return True
    if low.endswith(".com") or low.startswith("http://") or low.startswith("https://"):
        return True
    return False


def _extract_query_from_filename(path: Path) -> str:
    stem = path.stem.lower().strip()
    stem = re.sub(r"[_\-]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    if not stem:
        return "x feed"
    return stem[:80]


def _stable_hash(author: str, content: str, source_file: str) -> str:
    payload = f"{author}|{content}|{source_file}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parse_feed_text(raw: str, *, query: str, source_file: Path) -> List[XFeedRecord]:
    lines = [_normalize_line(line) for line in raw.splitlines()]
    lines = [line for line in lines if line]

    records: List[XFeedRecord] = []
    seen_hashes: set[str] = set()

    i = 0
    while i < len(lines):
        line = lines[i]
        if not re.fullmatch(r"@[A-Za-z0-9_]{2,32}", line):
            i += 1
            continue

        handle = line
        display = ""
        if i > 0:
            prev = lines[i - 1]
            if not _is_noise(prev) and not prev.startswith("@") and "·" not in prev:
                display = prev
        author = f"{display} {handle}".strip() if display else handle

        created_at_raw = ""
        content_parts: List[str] = []
        engagement_parts: List[str] = []
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            if re.fullmatch(r"@[A-Za-z0-9_]{2,32}", nxt):
                break
            if _is_noise(nxt):
                j += 1
                continue
            if "·" in nxt and len(nxt) <= 40 and not created_at_raw:
                created_at_raw = nxt
                j += 1
                continue
            if re.search(r"\bviews?\b|\blikes?\b|\bretweets?\b|\bkommentare?\b|\breply\b", nxt, re.IGNORECASE):
                engagement_parts.append(nxt)
                j += 1
                continue
            content_parts.append(nxt)
            j += 1

        content = " ".join(content_parts).strip()
        if len(content) < 24:
            i = j
            continue

        digest = _stable_hash(author, content, str(source_file))
        if digest in seen_hashes:
            i = j
            continue
        seen_hashes.add(digest)

        short_id = digest[:16]
        records.append(
            XFeedRecord(
                post_id=f"xfeed_{short_id}",
                author=author,
                created_at_raw=created_at_raw,
                content=content[:1200],
                query=query,
                source="x_feed_text",
                engagement_hints=" | ".join(engagement_parts)[:200],
                hash=digest,
            )
        )
        i = j

    return records


def _write_jsonl(path: Path, records: List[XFeedRecord]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec.__dict__, ensure_ascii=False) + "\n")


def ingest_x_feed_text(
    *,
    run_id: Optional[str] = None,
    source_dir: Optional[Path] = None,
    file_limit: int = 0,
) -> Tuple[List[Note], Path]:
    resolved_run_id = run_id or timestamp_id()
    base_dir = (source_dir or DEFAULT_X_FEED_DIR).expanduser().resolve()

    if not base_dir.exists():
        raise FileNotFoundError(f"X feed source directory not found: {base_dir}")

    files = sorted(
        [p for p in base_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".md"}],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if file_limit > 0:
        files = files[:file_limit]

    all_records: List[XFeedRecord] = []
    notes: List[Note] = []
    parsed_files: List[str] = []
    for path in files:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if not raw.strip():
            continue
        query = _extract_query_from_filename(path)
        parsed = _parse_feed_text(raw, query=query, source_file=path)
        if not parsed:
            continue
        parsed_files.append(str(path))
        all_records.extend(parsed)

        for rec in parsed:
            body = (
                f"[author] {rec.author}\n"
                f"[created_at_raw] {rec.created_at_raw}\n"
                f"[query] {rec.query}\n"
                f"[engagement_hints] {rec.engagement_hints}\n\n"
                f"{rec.content}"
            )
            notes.append(
                Note(
                    note_id=f"x_feed_text:{rec.post_id}",
                    title=f"{rec.author} | {rec.query}",
                    modified=_now_iso(),
                    body=body,
                    source="x_feed_text",
                )
            )

    run_dir = X_FEED_IMPORTS_DIR / resolved_run_id
    ensure_dir(run_dir)
    normalized_path = run_dir / "x_feed_text_normalized.jsonl"
    _write_jsonl(normalized_path, all_records)

    manifest = {
        "run_id": resolved_run_id,
        "imported_at": _now_iso(),
        "source_dir": str(base_dir),
        "parsed_files": parsed_files,
        "record_count": len(all_records),
        "normalized_path": str(normalized_path),
    }
    write_json(run_dir / "manifest.json", manifest)

    preview_lines = [
        f"# X Feed Text Ingest ({resolved_run_id})",
        "",
        f"- Source dir: {base_dir}",
        f"- Parsed files: {len(parsed_files)}",
        f"- Records: {len(all_records)}",
        "",
    ]
    for idx, rec in enumerate(all_records[:40], start=1):
        preview_lines.append(f"{idx}. {rec.author} | {rec.query} | {rec.content[:120]}")
    write_text(run_dir / "preview.md", "\n".join(preview_lines).strip() + "\n")

    return notes, normalized_path
