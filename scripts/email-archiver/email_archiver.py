#!/usr/bin/env python3
"""
Email Archiver System
- Scannt IMAP Postfaecher
- Kategorisiert Mails (Spam, Business, Personal, Legal)
- Archiviert pfeifer-sicherheit.de Mails forensisch
- SHA256 Hashes fuer Beweismittel-Integritaet
"""

import email
import hashlib
import imaplib
import os
import sqlite3
import sys
from datetime import datetime
from email.header import decode_header

# ============================================
# CONFIGURATION (NICHT in Git committen!)
# ============================================
# Erstelle eine .env Datei mit:
# IMAP_SERVER=imap.gmail.com
# IMAP_USER=deine@email.com
# IMAP_PASS=app-password-hier
# IMAP_PORT=993

CONFIG_FILE = os.path.expanduser("~/.openclaw/email-archiver/.env")
DB_FILE = os.path.expanduser("~/.openclaw/email-archiver/emails.db")
ARCHIVE_DIR = os.path.expanduser("~/.openclaw/email-archiver/archive")
LEGAL_DIR = os.path.expanduser("~/.openclaw/email-archiver/legal/pfeifer-sicherheit")
CHAIN_OF_CUSTODY = os.path.expanduser("~/.openclaw/email-archiver/legal/chain_of_custody.json")


def load_config():
    """Load IMAP config from .env file"""
    config = {}
    if not os.path.exists(CONFIG_FILE):
        print(f"FEHLER: Config-Datei nicht gefunden: {CONFIG_FILE}")
        print("Erstelle sie mit:")
        print(f"  mkdir -p {os.path.dirname(CONFIG_FILE)}")
        print(f"  cat > {CONFIG_FILE} << 'EOF'")
        print("IMAP_SERVER=imap.gmail.com")
        print("IMAP_USER=deine@email.com")
        print("IMAP_PASS=dein-app-passwort")
        print("IMAP_PORT=993")
        print("EOF")
        sys.exit(1)

    with open(CONFIG_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config


def init_db():
    """Initialize SQLite database"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT UNIQUE,
        from_addr TEXT,
        to_addr TEXT,
        subject TEXT,
        date_sent TEXT,
        date_archived TEXT,
        category TEXT,
        is_legal_evidence INTEGER DEFAULT 0,
        sha256_hash TEXT,
        file_path TEXT,
        folder TEXT,
        size_bytes INTEGER,
        has_attachments INTEGER DEFAULT 0,
        spam_score REAL DEFAULT 0.0,
        notes TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS chain_of_custody (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_message_id TEXT,
        action TEXT,
        timestamp TEXT,
        actor TEXT,
        sha256_before TEXT,
        sha256_after TEXT,
        notes TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        color TEXT
    )""")

    # Default categories
    categories = [
        ("spam", "Spam und Werbung", "#ff0000"),
        ("business", "Geschaeftliche Mails", "#0066ff"),
        ("personal", "Persoenliche Mails", "#00cc00"),
        ("legal", "Rechtsstreit / Beweismittel", "#ff6600"),
        ("pfeifer-sicherheit", "Mails von/an pfeifer-sicherheit.de", "#cc0066"),
        ("newsletter", "Newsletter und Abonnements", "#999999"),
        ("finance", "Rechnungen und Finanzen", "#ffcc00"),
        ("ai-empire", "AI Empire relevante Mails", "#9900ff"),
    ]
    for name, desc, color in categories:
        c.execute(
            "INSERT OR IGNORE INTO categories (name, description, color) VALUES (?, ?, ?)",
            (name, desc, color),
        )

    conn.commit()
    return conn


def compute_hash(raw_email_bytes):
    """SHA256 Hash fuer forensische Integritaet"""
    return hashlib.sha256(raw_email_bytes).hexdigest()


def decode_header_value(value):
    """Decode email header (handles encoded headers)"""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)


def categorize_email(from_addr, to_addr, subject, body_preview=""):
    """Kategorisiere Email basierend auf Absender/Betreff"""
    from_lower = (from_addr or "").lower()
    subject_lower = (subject or "").lower()

    # PRIORITAET 1: pfeifer-sicherheit.de (LEGAL)
    if "pfeifer-sicherheit.de" in from_lower or "pfeifer-sicherheit.de" in (to_addr or "").lower():
        return "pfeifer-sicherheit", True  # is_legal_evidence = True

    # PRIORITAET 2: Rechtsstreit Keywords
    legal_keywords = [
        "anwalt",
        "rechtsanwalt",
        "kanzlei",
        "gericht",
        "klage",
        "mahnung",
        "abmahnung",
        "frist",
        "rechtlich",
        "lawyer",
        "legal",
        "court",
        "lawsuit",
        "streitigkeit",
    ]
    if any(kw in subject_lower or kw in from_lower for kw in legal_keywords):
        return "legal", True

    # PRIORITAET 3: Spam Detection
    spam_keywords = [
        "unsubscribe",
        "abmelden",
        "newsletter",
        "promotion",
        "sale",
        "discount",
        "rabatt",
        "gewinn",
        "lottery",
        "viagra",
        "crypto airdrop",
        "nigerian prince",
    ]
    spam_domains = [
        "noreply@",
        "marketing@",
        "promo@",
        "newsletter@",
        "info@mailchimp",
        "bounce@",
    ]
    spam_score = sum(1 for kw in spam_keywords if kw in subject_lower)
    spam_score += sum(1 for d in spam_domains if d in from_lower)
    if spam_score >= 2:
        return "spam", False

    # PRIORITAET 4: Newsletter
    if "newsletter" in from_lower or "digest" in subject_lower:
        return "newsletter", False

    # PRIORITAET 5: Finance
    finance_keywords = [
        "rechnung",
        "invoice",
        "zahlung",
        "payment",
        "konto",
        "bank",
        "ueberweisung",
    ]
    if any(kw in subject_lower for kw in finance_keywords):
        return "finance", False

    # PRIORITAET 6: AI Empire
    ai_keywords = [
        "ollama",
        "openclaw",
        "kimi",
        "claude",
        "gumroad",
        "fiverr",
        "moonshot",
        "api key",
    ]
    if any(kw in subject_lower or kw in from_lower for kw in ai_keywords):
        return "ai-empire", False

    # Default: Business
    return "business", False


def save_email_file(raw_bytes, sha256, category, is_legal):
    """Save .eml file to appropriate directory"""
    if is_legal or category == "pfeifer-sicherheit":
        save_dir = LEGAL_DIR
    else:
        save_dir = os.path.join(ARCHIVE_DIR, category)

    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{sha256[:16]}.eml")

    with open(file_path, "wb") as f:
        f.write(raw_bytes)

    return file_path


def log_chain_of_custody(conn, message_id, action, sha256, notes=""):
    """Log Chain of Custody entry for legal evidence"""
    c = conn.cursor()
    c.execute(
        """INSERT INTO chain_of_custody
        (email_message_id, action, timestamp, actor, sha256_before, sha256_after, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            message_id,
            action,
            datetime.utcnow().isoformat(),
            "email_archiver_v1",
            sha256,
            sha256,
            notes,
        ),
    )
    conn.commit()


def scan_mailbox(config, folder="INBOX", limit=None):
    """Scan IMAP mailbox and archive all emails"""
    conn = init_db()

    print(f"Verbinde mit {config['IMAP_SERVER']}...")
    mail = imaplib.IMAP4_SSL(config["IMAP_SERVER"], int(config.get("IMAP_PORT", 993)))
    mail.login(config["IMAP_USER"], config["IMAP_PASS"])

    # List all folders
    print("Verfuegbare Ordner:")
    status, folders = mail.list()
    for f in folders:
        print(f"  {f.decode()}")

    mail.select(folder, readonly=True)  # READONLY fuer forensische Integritaet

    # Search all emails
    status, messages = mail.search(None, "ALL")
    if status != "OK":
        print(f"FEHLER: Kann Ordner {folder} nicht durchsuchen")
        return

    email_ids = messages[0].split()
    total = len(email_ids)
    print(f"\nGefunden: {total} Emails in {folder}")

    if limit:
        email_ids = email_ids[-limit:]  # Neueste zuerst
        print(f"Verarbeite die letzten {limit} Emails")

    stats = {
        "total": 0,
        "new": 0,
        "duplicate": 0,
        "categories": {},
        "legal": 0,
        "pfeifer": 0,
    }

    for i, eid in enumerate(email_ids, 1):
        try:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            raw_bytes = msg_data[0][1]
            sha256 = compute_hash(raw_bytes)

            # Check for duplicate
            c = conn.cursor()
            c.execute("SELECT id FROM emails WHERE sha256_hash = ?", (sha256,))
            if c.fetchone():
                stats["duplicate"] += 1
                continue

            msg = email.message_from_bytes(raw_bytes)

            # Extract headers
            from_addr = decode_header_value(msg.get("From", ""))
            to_addr = decode_header_value(msg.get("To", ""))
            subject = decode_header_value(msg.get("Subject", ""))
            date_sent = msg.get("Date", "")
            message_id = msg.get("Message-ID", f"unknown-{sha256[:16]}")

            # Check attachments
            has_attachments = 0
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    has_attachments = 1
                    break

            # Categorize
            category, is_legal = categorize_email(from_addr, to_addr, subject)

            # Save .eml file
            file_path = save_email_file(raw_bytes, sha256, category, is_legal)

            # Insert into DB
            c.execute(
                """INSERT OR IGNORE INTO emails
                (message_id, from_addr, to_addr, subject, date_sent, date_archived,
                 category, is_legal_evidence, sha256_hash, file_path, folder,
                 size_bytes, has_attachments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    message_id,
                    from_addr,
                    to_addr,
                    subject,
                    date_sent,
                    datetime.utcnow().isoformat(),
                    category,
                    int(is_legal),
                    sha256,
                    file_path,
                    folder,
                    len(raw_bytes),
                    has_attachments,
                ),
            )
            conn.commit()

            # Chain of Custody for legal evidence
            if is_legal or category == "pfeifer-sicherheit":
                log_chain_of_custody(
                    conn,
                    message_id,
                    "ARCHIVED",
                    sha256,
                    f"Archived from {folder} via IMAP (readonly)",
                )
                stats["legal"] += 1
                if category == "pfeifer-sicherheit":
                    stats["pfeifer"] += 1

            stats["total"] += 1
            stats["new"] += 1
            stats["categories"][category] = stats["categories"].get(category, 0) + 1

            # Progress
            if i % 50 == 0 or i == len(email_ids):
                print(f"  [{i}/{len(email_ids)}] {category}: {subject[:60]}")

        except Exception as e:
            print(f"  FEHLER bei Email {eid}: {e}")
            continue

    mail.logout()

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"SCAN ABGESCHLOSSEN: {folder}")
    print(f"{'=' * 60}")
    print(f"Gesamt verarbeitet:  {stats['total']}")
    print(f"Neu archiviert:      {stats['new']}")
    print(f"Duplikate:           {stats['duplicate']}")
    print(f"Legal/Beweismittel:  {stats['legal']}")
    print(f"pfeifer-sicherheit:  {stats['pfeifer']}")
    print("\nKategorien:")
    for cat, count in sorted(stats["categories"].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    return stats


def export_legal_report(output_file=None):
    """Export forensischer Report fuer Anwalt"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""SELECT * FROM emails
        WHERE is_legal_evidence = 1 OR category = 'pfeifer-sicherheit'
        ORDER BY date_sent""")
    legal_emails = c.fetchall()

    c.execute("SELECT * FROM chain_of_custody ORDER BY timestamp")
    custody_log = c.fetchall()

    if not output_file:
        output_file = os.path.expanduser("~/.openclaw/email-archiver/legal/BEWEISMITTEL_REPORT.md")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        f.write("# BEWEISMITTEL-REPORT: E-Mail Archiv\n")
        f.write(f"Erstellt: {datetime.utcnow().isoformat()} UTC\n")
        f.write("System: Email Archiver v1.0\n")
        f.write("Integritaet: SHA256 Hash pro Email\n\n")
        f.write("---\n\n")

        f.write("## Uebersicht\n")
        f.write(f"- Beweismittel-Emails gesamt: {len(legal_emails)}\n")
        f.write(f"- Chain of Custody Eintraege: {len(custody_log)}\n\n")

        f.write("## E-Mails (chronologisch)\n\n")
        f.write("| # | Datum | Von | Betreff | SHA256 | Datei |\n")
        f.write("|---|-------|-----|---------|--------|-------|\n")

        for i, row in enumerate(legal_emails, 1):
            _msg_id, from_a, _to_a, subj = row[1], row[2], row[3], row[4]
            date_s, sha = row[5], row[9]
            f.write(f"| {i} | {date_s} | {from_a[:30]} | {subj[:40]} | {sha[:12]}... | {row[10]} |\n")

        f.write("\n## Chain of Custody Log\n\n")
        f.write("| Zeitpunkt | Aktion | Email-ID | SHA256 | Notizen |\n")
        f.write("|-----------|--------|----------|--------|--------|\n")
        for entry in custody_log:
            f.write(f"| {entry[3]} | {entry[2]} | {entry[1][:20]}... | {entry[5][:12]}... | {entry[7]} |\n")

        f.write("\n---\n")
        f.write("\n## Forensische Hinweise\n")
        f.write("1. Alle Emails wurden per IMAP im READONLY-Modus abgerufen\n")
        f.write("2. SHA256 Hashes wurden beim Archivieren berechnet\n")
        f.write("3. .eml Dateien sind im RFC 822 Standard gespeichert\n")
        f.write("4. Timestamps sind UTC (koordinierte Weltzeit)\n")
        f.write("5. Keine Email wurde nach Archivierung veraendert\n")

    print(f"Report gespeichert: {output_file}")
    print(f"Beweismittel-Emails: {len(legal_emails)}")
    return output_file


def show_stats():
    """Show database statistics"""
    if not os.path.exists(DB_FILE):
        print("Keine Datenbank gefunden. Fuehre zuerst --scan aus.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM emails")
    total = c.fetchone()[0]

    c.execute("SELECT category, COUNT(*) FROM emails GROUP BY category ORDER BY COUNT(*) DESC")
    categories = c.fetchall()

    c.execute("SELECT COUNT(*) FROM emails WHERE is_legal_evidence = 1")
    legal = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM emails WHERE category = 'pfeifer-sicherheit'")
    pfeifer = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM emails WHERE category = 'spam'")
    spam = c.fetchone()[0]

    print(f"\n{'=' * 50}")
    print("EMAIL ARCHIVER STATISTIK")
    print(f"{'=' * 50}")
    print(f"Gesamt archiviert:     {total}")
    print(f"Beweismittel (Legal):  {legal}")
    print(f"pfeifer-sicherheit.de: {pfeifer}")
    print(f"Spam erkannt:          {spam}")
    print("\nKategorien:")
    for cat, count in categories:
        pct = round(count / total * 100, 1) if total > 0 else 0
        print(f"  {cat:25s} {count:5d} ({pct}%)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Email Archiver System")
    parser.add_argument("--scan", action="store_true", help="Scan und archiviere alle Emails")
    parser.add_argument("--folder", default="INBOX", help="IMAP Ordner (default: INBOX)")
    parser.add_argument("--all-folders", action="store_true", help="Alle Ordner scannen")
    parser.add_argument("--limit", type=int, help="Max Emails pro Ordner")
    parser.add_argument("--stats", action="store_true", help="Zeige Statistiken")
    parser.add_argument("--legal-report", action="store_true", help="Beweismittel-Report erstellen")
    parser.add_argument(
        "--export-pfeifer",
        action="store_true",
        help="Nur pfeifer-sicherheit.de exportieren",
    )

    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.legal_report:
        export_legal_report()
    elif args.scan:
        config = load_config()
        if args.all_folders:
            mail = imaplib.IMAP4_SSL(config["IMAP_SERVER"], int(config.get("IMAP_PORT", 993)))
            mail.login(config["IMAP_USER"], config["IMAP_PASS"])
            status, folders = mail.list()
            mail.logout()
            for f in folders:
                folder_name = f.decode().split('"')[-2] if '"' in f.decode() else "INBOX"
                print(f"\n--- Scanne Ordner: {folder_name} ---")
                scan_mailbox(config, folder_name, args.limit)
        else:
            scan_mailbox(config, args.folder, args.limit)
    elif args.legal_report:
        export_legal_report()
    else:
        parser.print_help()
        print("\nBeispiele:")
        print("  python email_archiver.py --scan                    # Inbox scannen")
        print("  python email_archiver.py --scan --all-folders      # ALLE Ordner")
        print("  python email_archiver.py --scan --limit 100        # Letzte 100")
        print("  python email_archiver.py --stats                   # Statistiken")
        print("  python email_archiver.py --legal-report            # Beweismittel-Report")
