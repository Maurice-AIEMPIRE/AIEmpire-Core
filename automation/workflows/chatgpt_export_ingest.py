from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from automation.utils.files import ensure_dir, timestamp_id, write_json, write_text
from automation.workflows.notes_ingest import Note


ROOT = Path(__file__).resolve().parents[2]
CHATGPT_EXPORTS_DIR = ROOT / "external" / "imports" / "chatgpt_exports"
DEFAULT_CHAT_EXPORT_DIR = ROOT / "claude_intake" / "chat_exports"
EXPORT_REGISTRY_PATH = CHATGPT_EXPORTS_DIR / "ingest_registry.json"
DOWNLOADS_DIR = Path.home() / "Downloads"
AUTO_ZIP_PATTERNS = (
    "*chatgpt*export*.zip",
    "*conversations*.zip",
    "*openai*.zip",
    "*chatgpt*.zip",
)


@dataclass
class MessageRecord:
    conversation_id: str
    message_id: str
    role: str
    created_at: str
    content: str
    source: str
    hash: str


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_registry() -> Dict[str, Any]:
    if not EXPORT_REGISTRY_PATH.exists():
        return {"updated_at": "", "entries": []}
    try:
        payload = json.loads(EXPORT_REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"updated_at": "", "entries": []}
    if not isinstance(payload, dict):
        return {"updated_at": "", "entries": []}
    entries = payload.get("entries")
    if not isinstance(entries, list):
        payload["entries"] = []
    return payload


def _save_registry(registry: Dict[str, Any]) -> None:
    ensure_dir(EXPORT_REGISTRY_PATH.parent)
    registry["updated_at"] = _now_iso()
    write_json(EXPORT_REGISTRY_PATH, registry)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_latest_zip(base_dir: Path) -> Optional[Path]:
    if not base_dir.exists() or not base_dir.is_dir():
        return None
    candidates: List[Path] = []
    for pattern in AUTO_ZIP_PATTERNS:
        candidates.extend(base_dir.glob(pattern))
    candidates = [p for p in candidates if p.is_file() and p.suffix.lower() == ".zip"]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _find_registry_entry_by_sha(registry: Dict[str, Any], sha256: str) -> Optional[Dict[str, Any]]:
    entries = registry.get("entries")
    if not isinstance(entries, list):
        return None
    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        if str(entry.get("sha256") or "") == sha256:
            return entry
    return None


def _resolve_source(
    *,
    run_id: str,
    export_zip: Optional[Path],
    export_dir: Optional[Path],
) -> Tuple[Path, str, Optional[str], Optional[Path], Dict[str, Any]]:
    """
    Resolve source in strict order:
      1) explicit --export-zip
      2) CHATGPT_EXPORT_ZIP env
      3) newest matching ZIP in ~/Downloads
      4) newest matching ZIP in claude_intake/chat_exports
      5) --export-dir
      6) default extracted chat export dir
    Returns:
      source_dir, source_label, source_sha256, source_zip_path, source_meta
    """
    registry = _load_registry()
    meta: Dict[str, Any] = {"selected_via": "", "reused": False, "duplicate_sha_skipped": False}

    resolved_zip: Optional[Path] = None
    if export_zip:
        resolved_zip = export_zip.expanduser().resolve()
        meta["selected_via"] = "arg_export_zip"
    else:
        env_zip_raw = str(os.environ.get("CHATGPT_EXPORT_ZIP", "")).strip()
        if env_zip_raw:
            resolved_zip = Path(env_zip_raw).expanduser().resolve()
            meta["selected_via"] = "env_CHATGPT_EXPORT_ZIP"
        else:
            latest_downloads = _find_latest_zip(DOWNLOADS_DIR)
            if latest_downloads:
                resolved_zip = latest_downloads
                meta["selected_via"] = "downloads_latest_zip"
            else:
                latest_intake = _find_latest_zip(DEFAULT_CHAT_EXPORT_DIR)
                if latest_intake:
                    resolved_zip = latest_intake
                    meta["selected_via"] = "intake_latest_zip"

    if resolved_zip:
        if not resolved_zip.exists():
            raise FileNotFoundError(f"ChatGPT export zip not found: {resolved_zip}")
        source_sha256 = _sha256_file(resolved_zip)
        existing = _find_registry_entry_by_sha(registry, source_sha256)
        if existing:
            existing_dir = Path(str(existing.get("source_dir") or "")).expanduser()
            if existing_dir.exists():
                meta["reused"] = True
                meta["duplicate_sha_skipped"] = True
                meta["existing_run_id"] = str(existing.get("run_id") or "")
                meta["existing_normalized_messages_path"] = str(existing.get("normalized_messages_path") or "")
                return (
                    existing_dir,
                    f"chatgpt_export_zip_reused:{resolved_zip.name}",
                    source_sha256,
                    resolved_zip,
                    meta,
                )

        source_dir = _extract_zip(resolved_zip, run_id)
        return (
            source_dir,
            f"chatgpt_export_zip:{resolved_zip.name}",
            source_sha256,
            resolved_zip,
            meta,
        )

    if export_dir:
        resolved_dir = export_dir.expanduser().resolve()
        meta["selected_via"] = "arg_export_dir"
    else:
        resolved_dir = DEFAULT_CHAT_EXPORT_DIR
        meta["selected_via"] = "default_export_dir"
    return resolved_dir, "chatgpt_export_dir", None, None, meta


def _ensure_iso_utc(value: Any) -> str:
    if value is None:
        return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")
        except Exception:
            return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

    raw = str(value).strip()
    if not raw:
        return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

    if raw.endswith("Z"):
        return raw

    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_to_dt(value: str) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def _parse_since_date(raw: Optional[str]) -> Optional[dt.datetime]:
    if not raw:
        return None
    try:
        parsed = dt.date.fromisoformat(raw.strip())
    except ValueError as exc:
        raise ValueError(f"Invalid since_date '{raw}'. Expected YYYY-MM-DD.") from exc
    return dt.datetime(parsed.year, parsed.month, parsed.day, tzinfo=dt.timezone.utc)


def _normalize_text(value: str, max_chars: int = 20000) -> str:
    text = " ".join(str(value or "").replace("\r", "\n").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 13].rstrip() + " [TRUNCATED]"


def _extract_content_text(message: Dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [str(item) for item in content if item is not None]
        return "\n".join(parts).strip()
    if isinstance(content, dict):
        parts = content.get("parts")
        if isinstance(parts, list):
            return "\n".join(str(part) for part in parts if part is not None).strip()
        text = content.get("text")
        if isinstance(text, str):
            return text
    return ""


def _stable_message_hash(
    conversation_id: str,
    role: str,
    created_at: str,
    content: str,
) -> str:
    payload = f"{conversation_id}|{role}|{created_at}|{_normalize_text(content, max_chars=6000)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _iter_conversations(payload: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
        return
    if not isinstance(payload, dict):
        return

    for key in ("conversations", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
            return

    if {"id", "mapping"} & set(payload.keys()):
        yield payload


def _parse_mapping_messages(conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        return []

    records: List[Dict[str, Any]] = []
    for node_id, node in mapping.items():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        author = message.get("author")
        role = ""
        if isinstance(author, dict):
            role = str(author.get("role") or "")
        if not role:
            role = str(message.get("role") or "unknown")
        role = role.strip().lower() or "unknown"

        created_at = _ensure_iso_utc(
            message.get("create_time")
            or message.get("update_time")
            or node.get("create_time")
            or node.get("update_time")
        )
        content = _extract_content_text(message)
        if not content.strip():
            continue

        message_id = str(message.get("id") or node_id or "")
        records.append(
            {
                "message_id": message_id,
                "role": role,
                "created_at": created_at,
                "content": content,
            }
        )

    records.sort(
        key=lambda item: (
            _iso_to_dt(str(item.get("created_at") or "")) or dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc),
            str(item.get("message_id") or ""),
        )
    )
    return records


def _parse_list_messages(conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("messages", "chat_messages"):
        value = conversation.get(key)
        if not isinstance(value, list):
            continue

        out: List[Dict[str, Any]] = []
        for idx, item in enumerate(value, start=1):
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or ((item.get("author") or {}).get("role") if isinstance(item.get("author"), dict) else "") or "unknown").strip().lower()
            content = str(item.get("content") or item.get("text") or "").strip()
            if not content:
                continue
            created_at = _ensure_iso_utc(item.get("create_time") or item.get("created_at") or item.get("timestamp"))
            message_id = str(item.get("id") or f"msg_{idx}")
            out.append(
                {
                    "message_id": message_id,
                    "role": role,
                    "created_at": created_at,
                    "content": content,
                }
            )
        if out:
            out.sort(
                key=lambda item: (
                    _iso_to_dt(str(item.get("created_at") or "")) or dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc),
                    str(item.get("message_id") or ""),
                )
            )
            return out

    return []


def _conversation_title(conversation: Dict[str, Any], conversation_id: str) -> str:
    title = str(conversation.get("title") or "").strip()
    if title:
        return title
    return f"ChatGPT Conversation {conversation_id[:12]}"


def _find_conversation_json_files(base_dir: Path) -> List[Path]:
    if not base_dir.exists():
        return []
    preferred: List[Path] = []
    fallback: List[Path] = []
    for path in sorted(base_dir.rglob("*.json")):
        name = path.name.lower()
        if name in {"conversations.json", "conversation.json", "chat.json"}:
            preferred.append(path)
        else:
            fallback.append(path)
    return preferred + fallback


def _extract_zip(zip_path: Path, run_id: str) -> Path:
    if not zip_path.exists():
        raise FileNotFoundError(f"ChatGPT export zip not found: {zip_path}")
    out_dir = CHATGPT_EXPORTS_DIR / run_id
    ensure_dir(out_dir)
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(out_dir)
    return out_dir


def _write_jsonl(path: Path, records: List[MessageRecord]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record.__dict__, ensure_ascii=False) + "\n")


def _records_to_notes(
    grouped: Dict[str, Dict[str, Any]],
    *,
    source_label: str,
    conversation_limit: int = 0,
    since_date: Optional[dt.datetime] = None,
) -> Tuple[List[Note], List[Dict[str, Any]]]:
    notes: List[Note] = []
    meta: List[Dict[str, Any]] = []
    conversations: List[Tuple[str, Dict[str, Any]]] = sorted(
        grouped.items(),
        key=lambda item: (
            _iso_to_dt(str(item[1].get("latest_created_at") or "")) or dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
        ),
        reverse=True,
    )

    if conversation_limit > 0:
        conversations = conversations[:conversation_limit]

    for conversation_id, payload in conversations:
        latest_dt = _iso_to_dt(str(payload.get("latest_created_at") or ""))
        if since_date and latest_dt and latest_dt < since_date:
            continue

        messages = payload.get("messages") or []
        if not messages:
            continue

        lines = [f"# {payload.get('title') or conversation_id}", ""]
        for item in messages:
            role = str(item.get("role") or "unknown")
            created_at = str(item.get("created_at") or "")
            content = str(item.get("content") or "").strip()
            if not content:
                continue
            lines.append(f"[{role} | {created_at}]")
            lines.append(content)
            lines.append("")

        body = "\n".join(lines).strip()
        modified = str(payload.get("latest_created_at") or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"))
        note_id = f"chatgpt_export:{conversation_id}"
        notes.append(
            Note(
                note_id=note_id,
                title=str(payload.get("title") or conversation_id),
                modified=modified,
                body=body,
                source=source_label,
            )
        )
        meta.append(
            {
                "conversation_id": conversation_id,
                "title": str(payload.get("title") or ""),
                "latest_created_at": modified,
                "message_count": len(messages),
            }
        )

    return notes, meta


def ingest_chatgpt_export(
    *,
    run_id: Optional[str] = None,
    export_zip: Optional[Path] = None,
    export_dir: Optional[Path] = None,
    conversation_limit: int = 0,
    since_date: Optional[str] = None,
) -> Tuple[List[Note], Path]:
    """
    Parse a ChatGPT data export and return synthesized notes for nugget extraction.
    Also writes normalized JSONL records for downstream analytics.
    """
    resolved_run_id = run_id or timestamp_id()
    since_dt = _parse_since_date(since_date)
    source_dir, source_label, source_sha256, source_zip_path, source_meta = _resolve_source(
        run_id=resolved_run_id,
        export_zip=export_zip,
        export_dir=export_dir,
    )

    records_dir = CHATGPT_EXPORTS_DIR / resolved_run_id
    ensure_dir(records_dir)
    if bool((source_meta or {}).get("duplicate_sha_skipped")):
        existing_norm = Path(str((source_meta or {}).get("existing_normalized_messages_path") or "")).expanduser()
        if not existing_norm.exists():
            existing_norm = records_dir / "normalized_messages.jsonl"
            _write_jsonl(existing_norm, [])
        manifest = {
            "run_id": resolved_run_id,
            "imported_at": _now_iso(),
            "source_dir": str(source_dir),
            "source_label": source_label,
            "source_zip_path": str(source_zip_path) if source_zip_path else "",
            "source_sha256": source_sha256 or "",
            "source_meta": source_meta,
            "parsed_files": [],
            "conversation_count": 0,
            "message_count": 0,
            "normalized_messages_path": str(existing_norm),
            "since_date": since_date or "",
            "conversation_limit": int(max(0, conversation_limit)),
            "conversations": [],
            "duplicate_skipped": True,
        }
        write_json(records_dir / "manifest.json", manifest)
        preview_lines = [
            f"# ChatGPT Export Ingest ({resolved_run_id})",
            "",
            "- Duplicate ZIP SHA256 detected.",
            f"- Reused source: {source_dir}",
            f"- Existing run: {str((source_meta or {}).get('existing_run_id') or '')}",
            "",
        ]
        write_text(records_dir / "conversation_preview.md", "\n".join(preview_lines).strip() + "\n")
        if source_sha256:
            registry = _load_registry()
            entries = registry.get("entries")
            if not isinstance(entries, list):
                entries = []
                registry["entries"] = entries
            entries.append(
                {
                    "run_id": resolved_run_id,
                    "imported_at": manifest["imported_at"],
                    "sha256": source_sha256,
                    "zip_path": str(source_zip_path) if source_zip_path else "",
                    "source_dir": str(source_dir),
                    "conversation_count": 0,
                    "message_count": 0,
                    "normalized_messages_path": str(existing_norm),
                    "selected_via": str((source_meta or {}).get("selected_via") or ""),
                    "reused": True,
                    "duplicate_skipped": True,
                    "existing_run_id": str((source_meta or {}).get("existing_run_id") or ""),
                }
            )
            registry["entries"] = entries[-400:]
            _save_registry(registry)
        return [], existing_norm

    if not source_dir.exists():
        selected_via = str((source_meta or {}).get("selected_via") or "")
        if selected_via in {"default_export_dir", "downloads_latest_zip", "intake_latest_zip", "env_CHATGPT_EXPORT_ZIP"}:
            normalized_path = records_dir / "normalized_messages.jsonl"
            _write_jsonl(normalized_path, [])
            manifest = {
                "run_id": resolved_run_id,
                "imported_at": _now_iso(),
                "source_dir": str(source_dir),
                "source_label": source_label,
                "source_zip_path": str(source_zip_path) if source_zip_path else "",
                "source_sha256": source_sha256 or "",
                "source_meta": source_meta,
                "parsed_files": [],
                "conversation_count": 0,
                "message_count": 0,
                "normalized_messages_path": str(normalized_path),
                "since_date": since_date or "",
                "conversation_limit": int(max(0, conversation_limit)),
                "conversations": [],
                "status": "no_source_found",
            }
            write_json(records_dir / "manifest.json", manifest)
            write_text(
                records_dir / "conversation_preview.md",
                (
                    f"# ChatGPT Export Ingest ({resolved_run_id})\n\n"
                    f"- No source found for selected mode: {selected_via}\n"
                    f"- Checked path: {source_dir}\n"
                ),
            )
            return [], normalized_path
        raise FileNotFoundError(f"ChatGPT export directory not found: {source_dir}")

    json_files = _find_conversation_json_files(source_dir)
    if not json_files:
        raise FileNotFoundError(
            f"No JSON files found in ChatGPT export source: {source_dir}. "
            "Expected conversations.json or equivalent JSON files."
        )

    grouped: Dict[str, Dict[str, Any]] = {}
    all_records: List[MessageRecord] = []
    seen_hashes = set()
    parsed_files: List[str] = []

    for json_path in json_files:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        conversations = list(_iter_conversations(payload))
        if not conversations:
            continue
        parsed_files.append(str(json_path))

        for conv in conversations:
            conversation_id = str(conv.get("id") or conv.get("conversation_id") or "").strip() or hashlib.sha1(
                json.dumps(conv, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()[:16]
            title = _conversation_title(conv, conversation_id)

            messages = _parse_mapping_messages(conv)
            if not messages:
                messages = _parse_list_messages(conv)
            if not messages:
                continue

            slot = grouped.setdefault(
                conversation_id,
                {
                    "title": title,
                    "messages": [],
                    "latest_created_at": "",
                },
            )
            if not slot.get("title"):
                slot["title"] = title

            for msg in messages:
                created_at = _ensure_iso_utc(msg.get("created_at"))
                content = _normalize_text(str(msg.get("content") or ""))
                role = str(msg.get("role") or "unknown").strip().lower() or "unknown"
                message_id = str(msg.get("message_id") or hashlib.sha1(content.encode("utf-8")).hexdigest()[:12])
                digest = _stable_message_hash(conversation_id, role, created_at, content)
                if digest in seen_hashes:
                    continue
                seen_hashes.add(digest)

                record = MessageRecord(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    role=role,
                    created_at=created_at,
                    content=content,
                    source=source_label,
                    hash=digest,
                )
                all_records.append(record)
                slot["messages"].append(
                    {
                        "message_id": message_id,
                        "role": role,
                        "created_at": created_at,
                        "content": content,
                    }
                )
                latest = str(slot.get("latest_created_at") or "")
                if not latest or (created_at > latest):
                    slot["latest_created_at"] = created_at

    for payload in grouped.values():
        payload["messages"].sort(
            key=lambda item: (
                _iso_to_dt(str(item.get("created_at") or "")) or dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc),
                str(item.get("message_id") or ""),
            )
        )

    normalized_path = records_dir / "normalized_messages.jsonl"
    _write_jsonl(normalized_path, all_records)

    notes, conversation_meta = _records_to_notes(
        grouped,
        source_label=source_label,
        conversation_limit=max(0, int(conversation_limit)),
        since_date=since_dt,
    )

    manifest = {
        "run_id": resolved_run_id,
        "imported_at": _now_iso(),
        "source_dir": str(source_dir),
        "source_label": source_label,
        "source_zip_path": str(source_zip_path) if source_zip_path else "",
        "source_sha256": source_sha256 or "",
        "source_meta": source_meta,
        "parsed_files": parsed_files,
        "conversation_count": len(conversation_meta),
        "message_count": len(all_records),
        "normalized_messages_path": str(normalized_path),
        "since_date": since_date or "",
        "conversation_limit": int(max(0, conversation_limit)),
        "conversations": conversation_meta,
    }
    write_json(records_dir / "manifest.json", manifest)

    if source_sha256:
        registry = _load_registry()
        entries = registry.get("entries")
        if not isinstance(entries, list):
            entries = []
            registry["entries"] = entries
        entries.append(
            {
                "run_id": resolved_run_id,
                "imported_at": manifest["imported_at"],
                "sha256": source_sha256,
                "zip_path": str(source_zip_path) if source_zip_path else "",
                "source_dir": str(source_dir),
                "conversation_count": len(conversation_meta),
                "message_count": len(all_records),
                "normalized_messages_path": str(normalized_path),
                "selected_via": str((source_meta or {}).get("selected_via") or ""),
                "reused": bool((source_meta or {}).get("reused")),
            }
        )
        registry["entries"] = entries[-400:]
        _save_registry(registry)

    preview_lines = [
        f"# ChatGPT Export Ingest ({resolved_run_id})",
        "",
        f"- Source dir: {source_dir}",
        f"- Parsed files: {len(parsed_files)}",
        f"- Conversations: {len(conversation_meta)}",
        f"- Messages (deduped): {len(all_records)}",
        "",
    ]
    for idx, item in enumerate(conversation_meta[:50], start=1):
        preview_lines.append(
            f"{idx}. {item.get('title', 'untitled')} | messages={item.get('message_count', 0)} | latest={item.get('latest_created_at', '')}"
        )
    write_text(records_dir / "conversation_preview.md", "\n".join(preview_lines).strip() + "\n")

    return notes, normalized_path
