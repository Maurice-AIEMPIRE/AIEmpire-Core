"""
Empire Datenbank — SQLite mit Volltextsuche
============================================
Speichert ALLE analysierten Dokumente persistent.
Jedes Dokument einmal verarbeitet (Hash-basierte Deduplizierung).

Schema:
  documents     — Haupt-Tabelle (ein Eintrag pro Datei)
  documents_fts — Volltextsuche (SQLite FTS5)
  tags          — Tag-Index für schnelle Filterung

Exports für iCloud:
  export_to_json()     → alle_dokumente.json
  export_to_markdown() → _Datenbank_Uebersicht.md
  export_csv()         → datenbank_export.csv
"""

import csv
import hashlib
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = Path("/data/empire.db")
EXPORT_DIR = Path("/data/results/_Datenbank")


def _get_conn(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Erstelle Verbindung mit Row-Factory für Dict-Zugriff."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # Crash-safe Schreibmodus
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """Erstelle Datenbank-Schema (idempotent — kann mehrfach aufgerufen werden)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn(db_path)
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name               TEXT NOT NULL,
                file_hash               TEXT UNIQUE,
                file_type               TEXT,
                processed_at            TEXT NOT NULL,

                -- AI-Klassifikation
                icloud_folder           TEXT,
                document_type           TEXT,
                importance              TEXT,
                sentiment               TEXT,
                language                TEXT,
                has_personal_data       INTEGER DEFAULT 0,
                follow_up_needed        INTEGER DEFAULT 0,
                consensus_score         REAL,

                -- Texte
                summary                 TEXT,
                detailed_summary        TEXT,
                keywords                TEXT,
                tags                    TEXT,
                insights                TEXT,
                actions                 TEXT,
                risks                   TEXT,
                recommendations         TEXT,
                entities                TEXT,

                -- Performance
                analysis_time_s         REAL,
                pipeline                TEXT,

                -- Original-Vorschau (erste 500 Zeichen)
                content_preview         TEXT,

                -- Raw AI Output (für spätere Neu-Auswertung)
                layer1_raw              TEXT,
                layer2_raw              TEXT,
                layer3_raw              TEXT
            );

            -- Volltextsuche über alle relevanten Felder
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                file_name,
                summary,
                detailed_summary,
                keywords,
                insights,
                content_preview,
                content='documents',
                content_rowid='id',
                tokenize='unicode61'
            );

            -- FTS automatisch befüllen
            CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(rowid, file_name, summary, detailed_summary,
                    keywords, insights, content_preview)
                VALUES (new.id, new.file_name, new.summary, new.detailed_summary,
                    new.keywords, new.insights, new.content_preview);
            END;

            CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, file_name, summary,
                    detailed_summary, keywords, insights, content_preview)
                VALUES ('delete', old.id, old.file_name, old.summary, old.detailed_summary,
                    old.keywords, old.insights, old.content_preview);
                INSERT INTO documents_fts(rowid, file_name, summary, detailed_summary,
                    keywords, insights, content_preview)
                VALUES (new.id, new.file_name, new.summary, new.detailed_summary,
                    new.keywords, new.insights, new.content_preview);
            END;

            -- Tag-Index für schnelle Filterung
            CREATE TABLE IF NOT EXISTS tags (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                tag         TEXT NOT NULL,
                UNIQUE(document_id, tag)
            );
            CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
            CREATE INDEX IF NOT EXISTS idx_docs_folder ON documents(icloud_folder);
            CREATE INDEX IF NOT EXISTS idx_docs_importance ON documents(importance);
            CREATE INDEX IF NOT EXISTS idx_docs_processed ON documents(processed_at);
            CREATE INDEX IF NOT EXISTS idx_docs_type ON documents(document_type);
        """)
    conn.close()
    logger.info(f"Datenbank bereit: {db_path}")


def _file_hash(file_path: str) -> str:
    """SHA-256 Hash einer Datei für Deduplizierung."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except Exception:
        # Fallback: Hash des Dateinamens + Größe
        p = Path(file_path)
        h.update(f"{p.name}{p.stat().st_size if p.exists() else 0}".encode())
    return h.hexdigest()


def already_processed(file_path: str, db_path: Path = DB_PATH) -> bool:
    """Prüfe ob Datei bereits in der Datenbank ist (via Hash)."""
    fhash = _file_hash(file_path)
    conn = _get_conn(db_path)
    row = conn.execute(
        "SELECT id FROM documents WHERE file_hash = ?", (fhash,)
    ).fetchone()
    conn.close()
    return row is not None


def save_document(
    file_path: str,
    extracted: dict[str, Any],
    analysis: dict[str, Any],
    db_path: Path = DB_PATH,
) -> int:
    """
    Speichere analysiertes Dokument in der Datenbank.
    Gibt die neue ID zurück (oder -1 bei Duplikat).
    """
    fhash = _file_hash(file_path)
    final = analysis.get("final", {})
    qwen = analysis.get("layer1_qwen", {})
    deepseek = analysis.get("layer2_deepseek", {})
    verified = analysis.get("layer3_verified", {})

    # Content-Vorschau
    content_preview = ""
    ct = extracted.get("content_type", "")
    if ct == "pdf":
        pages = extracted.get("text", [])
        content_preview = " ".join(p.get("content", "") for p in pages)[:500]
    elif ct in ("docx", "xlsx", "office"):
        content_preview = str(extracted.get("text", ""))[:500]
    elif ct == "csv":
        content_preview = json.dumps(extracted.get("sample_rows", []))[:500]
    elif ct == "audio":
        content_preview = str(extracted.get("transcription", ""))[:500]
    elif ct == "image":
        content_preview = str(extracted.get("ocr_text", ""))[:500]

    row = {
        "file_name":        extracted.get("file_name", Path(file_path).name),
        "file_hash":        fhash,
        "file_type":        extracted.get("file_type", ""),
        "processed_at":     datetime.now().isoformat(),
        "icloud_folder":    final.get("icloud_folder", "Sonstiges"),
        "document_type":    final.get("document_type", "Sonstiges"),
        "importance":       final.get("importance", "mittel"),
        "sentiment":        qwen.get("sentiment", "neutral"),
        "language":         qwen.get("language", "de"),
        "has_personal_data": 1 if final.get("has_personal_data") else 0,
        "follow_up_needed": 1 if final.get("follow_up_needed") else 0,
        "consensus_score":  verified.get("consensus_score", 0.0),
        "summary":          final.get("summary", ""),
        "detailed_summary": deepseek.get("detailed_summary", ""),
        "keywords":         json.dumps(final.get("keywords", []), ensure_ascii=False),
        "tags":             json.dumps(final.get("tags", []), ensure_ascii=False),
        "insights":         json.dumps(final.get("insights", []), ensure_ascii=False),
        "actions":          json.dumps(final.get("actions", []), ensure_ascii=False),
        "risks":            json.dumps(deepseek.get("risks_and_issues", []), ensure_ascii=False),
        "recommendations":  json.dumps(deepseek.get("recommendations", []), ensure_ascii=False),
        "entities":         json.dumps(deepseek.get("entities", {}), ensure_ascii=False),
        "analysis_time_s":  analysis.get("total_analysis_time_s", 0.0),
        "pipeline":         analysis.get("pipeline", ""),
        "content_preview":  content_preview,
        "layer1_raw":       json.dumps(analysis.get("layer1_qwen", {}), ensure_ascii=False),
        "layer2_raw":       json.dumps(analysis.get("layer2_deepseek", {}), ensure_ascii=False),
        "layer3_raw":       json.dumps(analysis.get("layer3_verified", {}), ensure_ascii=False),
    }

    conn = _get_conn(db_path)
    try:
        with conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO documents (
                    file_name, file_hash, file_type, processed_at,
                    icloud_folder, document_type, importance, sentiment, language,
                    has_personal_data, follow_up_needed, consensus_score,
                    summary, detailed_summary, keywords, tags, insights, actions,
                    risks, recommendations, entities,
                    analysis_time_s, pipeline, content_preview,
                    layer1_raw, layer2_raw, layer3_raw
                ) VALUES (
                    :file_name, :file_hash, :file_type, :processed_at,
                    :icloud_folder, :document_type, :importance, :sentiment, :language,
                    :has_personal_data, :follow_up_needed, :consensus_score,
                    :summary, :detailed_summary, :keywords, :tags, :insights, :actions,
                    :risks, :recommendations, :entities,
                    :analysis_time_s, :pipeline, :content_preview,
                    :layer1_raw, :layer2_raw, :layer3_raw
                )
            """, row)
            doc_id = cursor.lastrowid or -1

            if doc_id > 0:
                # Tags in Tag-Tabelle
                for tag in final.get("tags", []):
                    conn.execute(
                        "INSERT OR IGNORE INTO tags (document_id, tag) VALUES (?, ?)",
                        (doc_id, str(tag).lower())
                    )
                logger.info(f"DB: Gespeichert [{doc_id}] {row['file_name']}")
            else:
                logger.info(f"DB: Duplikat übersprungen: {row['file_name']}")

        return doc_id
    finally:
        conn.close()


def search(
    query: str,
    folder: str | None = None,
    importance: str | None = None,
    limit: int = 20,
    db_path: Path = DB_PATH,
) -> list[dict]:
    """
    Volltextsuche in der Datenbank.

    Args:
        query:      Suchbegriff (Volltext oder '*' für alle)
        folder:     Filter nach iCloud-Ordner (z.B. 'Rechnungen')
        importance: Filter nach Wichtigkeit ('hoch', 'mittel', 'niedrig')
        limit:      Max. Ergebnisse

    Returns:
        Liste von Dokumenten als Dict
    """
    conn = _get_conn(db_path)
    try:
        if query and query != "*":
            sql = """
                SELECT d.* FROM documents d
                JOIN documents_fts fts ON d.id = fts.rowid
                WHERE documents_fts MATCH ?
            """
            params: list = [query]
        else:
            sql = "SELECT * FROM documents WHERE 1=1"
            params = []

        if folder:
            sql += " AND d.icloud_folder = ?" if "fts" in sql else " AND icloud_folder = ?"
            params.append(folder)
        if importance:
            sql += " AND d.importance = ?" if "fts" in sql else " AND importance = ?"
            params.append(importance)

        sql += " ORDER BY d.processed_at DESC LIMIT ?" if "fts" in sql else " ORDER BY processed_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats(db_path: Path = DB_PATH) -> dict:
    """Statistiken über die Datenbank."""
    conn = _get_conn(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        by_folder = dict(conn.execute(
            "SELECT icloud_folder, COUNT(*) FROM documents GROUP BY icloud_folder"
        ).fetchall())
        by_importance = dict(conn.execute(
            "SELECT importance, COUNT(*) FROM documents GROUP BY importance"
        ).fetchall())
        by_type = dict(conn.execute(
            "SELECT document_type, COUNT(*) FROM documents GROUP BY document_type ORDER BY COUNT(*) DESC LIMIT 10"
        ).fetchall())
        top_tags = conn.execute(
            "SELECT tag, COUNT(*) as cnt FROM tags GROUP BY tag ORDER BY cnt DESC LIMIT 20"
        ).fetchall()
        needs_followup = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE follow_up_needed = 1"
        ).fetchone()[0]
        has_personal = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE has_personal_data = 1"
        ).fetchone()[0]
        last_processed = conn.execute(
            "SELECT processed_at FROM documents ORDER BY processed_at DESC LIMIT 1"
        ).fetchone()

        return {
            "total_documents": total,
            "by_folder": by_folder,
            "by_importance": by_importance,
            "by_document_type": by_type,
            "top_tags": [{"tag": r[0], "count": r[1]} for r in top_tags],
            "needs_followup": needs_followup,
            "has_personal_data": has_personal,
            "last_processed": last_processed[0] if last_processed else None,
            "db_path": str(db_path),
            "db_size_mb": round(db_path.stat().st_size / 1024 / 1024, 2) if db_path.exists() else 0,
        }
    finally:
        conn.close()


# ─── Exports für iCloud ───────────────────────────────────────────────────────

def export_to_json(
    export_dir: Path = EXPORT_DIR,
    db_path: Path = DB_PATH,
) -> str:
    """Exportiere alle Dokumente als JSON (für iCloud)."""
    export_dir.mkdir(parents=True, exist_ok=True)

    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT * FROM documents ORDER BY processed_at DESC"
    ).fetchall()
    conn.close()

    data = {
        "exported_at": datetime.now().isoformat(),
        "total": len(rows),
        "documents": [dict(r) for r in rows],
    }

    path = export_dir / "alle_dokumente.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"JSON-Export: {path} ({len(rows)} Dokumente)")
    return str(path)


def export_to_csv(
    export_dir: Path = EXPORT_DIR,
    db_path: Path = DB_PATH,
) -> str:
    """Exportiere als CSV (öffnet sich in Excel)."""
    export_dir.mkdir(parents=True, exist_ok=True)

    conn = _get_conn(db_path)
    rows = conn.execute("""
        SELECT
            file_name, file_type, document_type, icloud_folder,
            importance, sentiment, language,
            has_personal_data, follow_up_needed, consensus_score,
            summary, keywords, tags, analysis_time_s, processed_at
        FROM documents ORDER BY processed_at DESC
    """).fetchall()
    conn.close()

    path = export_dir / "datenbank_export.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig = Excel-kompatibel
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Dateiname", "Typ", "Dokument-Typ", "Ordner",
            "Wichtigkeit", "Stimmung", "Sprache",
            "Personendaten", "Follow-up", "Konsens",
            "Zusammenfassung", "Keywords", "Tags", "Analyse-Zeit (s)", "Verarbeitet am"
        ])
        for r in rows:
            writer.writerow(list(r))

    logger.info(f"CSV-Export: {path} ({len(rows)} Zeilen)")
    return str(path)


def export_to_markdown(
    export_dir: Path = EXPORT_DIR,
    db_path: Path = DB_PATH,
) -> str:
    """Exportiere als lesbares Markdown mit Statistiken + Tabelle."""
    export_dir.mkdir(parents=True, exist_ok=True)
    stats = get_stats(db_path)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    conn = _get_conn(db_path)
    recent = conn.execute(
        "SELECT * FROM documents ORDER BY processed_at DESC LIMIT 50"
    ).fetchall()
    high_prio = conn.execute(
        "SELECT * FROM documents WHERE importance = 'hoch' ORDER BY processed_at DESC"
    ).fetchall()
    followups = conn.execute(
        "SELECT * FROM documents WHERE follow_up_needed = 1 ORDER BY processed_at DESC"
    ).fetchall()
    conn.close()

    md = f"""# AIEmpire Datenbank-Übersicht

**Stand:** {now}
**Gesamt:** {stats['total_documents']} Dokumente
**Größe:** {stats['db_size_mb']} MB

---

## Statistiken

| Ordner | Anzahl |
|--------|--------|
"""
    for folder, count in sorted(stats["by_folder"].items(), key=lambda x: -x[1]):
        md += f"| {folder} | {count} |\n"

    md += f"""
| Wichtigkeit | Anzahl |
|-------------|--------|
"""
    for imp, count in stats["by_importance"].items():
        badge = {"hoch": "🔴", "mittel": "🟡", "niedrig": "🟢"}.get(imp, "")
        md += f"| {badge} {imp} | {count} |\n"

    md += f"""
**Follow-up nötig:** {stats['needs_followup']} Dokumente
**Mit Personendaten:** {stats['has_personal_data']} Dokumente

**Top Tags:** {', '.join(f"`{t['tag']}`" for t in stats['top_tags'][:10])}

---

"""

    # Hochpriorität zuerst
    if high_prio:
        md += "## 🔴 Hochpriorität\n\n"
        md += "| Datei | Typ | Ordner | Zusammenfassung |\n|-------|-----|--------|----------------|\n"
        for r in high_prio:
            summary = (r["summary"] or "")[:80].replace("|", "/")
            md += f"| {r['file_name']} | {r['document_type']} | {r['icloud_folder']} | {summary}... |\n"
        md += "\n---\n\n"

    # Follow-ups
    if followups:
        md += "## ⚠️ Follow-up nötig\n\n"
        for r in followups:
            md += f"- **{r['file_name']}** ({r['icloud_folder']}) — {(r['summary'] or '')[:100]}\n"
        md += "\n---\n\n"

    # Alle neuesten 50
    md += "## Neueste Dokumente\n\n"
    md += "| Datum | Datei | Typ | Ordner | Wichtigkeit |\n|-------|-------|-----|--------|-------------|\n"
    for r in recent:
        date = (r["processed_at"] or "")[:10]
        imp = {"hoch": "🔴", "mittel": "🟡", "niedrig": "🟢"}.get(r["importance"] or "", "")
        md += f"| {date} | {r['file_name']} | {r['document_type']} | {r['icloud_folder']} | {imp} {r['importance']} |\n"

    md += "\n---\n*Generiert von AIEmpire Data Pipeline*\n"

    path = export_dir / "_Datenbank_Uebersicht.md"
    path.write_text(md, encoding="utf-8")
    logger.info(f"Markdown-Export: {path}")
    return str(path)


def run_exports(
    export_dir: Path = EXPORT_DIR,
    db_path: Path = DB_PATH,
) -> dict[str, str]:
    """Führe alle Exports aus."""
    return {
        "json":     export_to_json(export_dir, db_path),
        "csv":      export_to_csv(export_dir, db_path),
        "markdown": export_to_markdown(export_dir, db_path),
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    init_db()

    if cmd == "stats":
        print(json.dumps(get_stats(), indent=2, ensure_ascii=False))
    elif cmd == "search":
        q = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "*"
        results = search(q)
        for r in results:
            print(f"[{r['importance']}] {r['file_name']} — {(r['summary'] or '')[:100]}")
    elif cmd == "export":
        paths = run_exports()
        for fmt, path in paths.items():
            print(f"{fmt}: {path}")
    else:
        print("Befehle: stats, search <query>, export")
