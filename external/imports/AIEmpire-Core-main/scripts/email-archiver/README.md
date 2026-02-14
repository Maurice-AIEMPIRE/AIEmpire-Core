# Email Archiver System
# Fuer Maurice's AI Empire + Rechtsstreit pfeifer-sicherheit.de

## Features
- IMAP-basiertes Email Scanning
- Automatische Kategorisierung (Spam, Business, Personal, Legal)
- pfeifer-sicherheit.de Mails separat + forensisch gesichert
- SHA256 Hashes fuer Beweismittel-Integritaet
- Chain of Custody Dokumentation
- Lokale SQLite Datenbank (kein Cloud-Abhaengigkeit)

## Setup
1. Python venv aktivieren
2. IMAP Credentials eintragen (NICHT in Git!)
3. `python email_archiver.py --scan` ausfuehren
4. Dashboard: `python email_dashboard.py`

## Rechtliche Hinweise
- Alle Mails werden mit SHA256 Hash gesichert
- Timestamps werden UTC gespeichert
- Keine Veraenderung nach Archivierung moeglich
- Export als .eml (RFC 822 Standard) fuer Anwaelte
