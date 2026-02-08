# Chat Export Tool - Dokumentation

> Konvertiere ChatGPT/Claude Exports in saubere TXT/Markdown/Word Formate

## 📋 Übersicht

Das Chat Export Tool (`chat_export_tool.py`) erstellt saubere, strukturierte Dokumente aus Chat-Verläufen. Perfekt für:

- 📝 Dokumentation von AI-Gesprächen
- 💾 Backup von wertvollen Konversationen
- 📊 Analyse von Chat-Sessions
- 📤 Teilen von Erkenntnissen im Team

## 🚀 Quick Start

### 1. Beispiel-Export generieren

```bash
python3 chat_export_tool.py --example
```

Erstellt Beispiel-Exports in allen Formaten:
- `exports/chat_export_YYYY-MM-DD_HH-MM-SS.txt`
- `exports/chat_export_YYYY-MM-DD_HH-MM-SS.md`
- `exports/chat_export_YYYY-MM-DD_HH-MM-SS_word.md`

### 2. ChatGPT Export konvertieren

**Schritt 1:** ChatGPT Export herunterladen
1. ChatGPT → Settings → Data controls → Export data
2. Warten auf Email mit Download-Link
3. ZIP herunterladen und entpacken
4. `conversations.json` finden

**Schritt 2:** Konvertieren
```bash
python3 chat_export_tool.py conversations.json -t "Maurice AI Empire Sessions"
```

### 3. Einfache Text-Datei konvertieren

```bash
python3 chat_export_tool.py my_chat.txt -f md -t "Projekt Diskussion"
```

## 📖 Verwendung

### Alle Optionen

```bash
python3 chat_export_tool.py [INPUT_FILE] [OPTIONS]
```

**Optionen:**

| Option | Beschreibung | Default |
|--------|--------------|---------|
| `-f, --format` | Export-Format: `txt`, `md`, `word`, `all` | `all` |
| `-o, --output-dir` | Output-Verzeichnis | `exports/` |
| `-t, --title` | Titel für den Export | `Chat Export` |
| `--example` | Beispiel-Export generieren | - |

### Beispiele

#### Nur Markdown Export
```bash
python3 chat_export_tool.py chat.json -f md
```

#### Eigenes Output-Verzeichnis
```bash
python3 chat_export_tool.py chat.json -o /tmp/my-exports
```

#### Mit Custom Titel
```bash
python3 chat_export_tool.py chat.json -t "OpenClaw Implementation Discussion"
```

## 📄 Export-Formate

### 1. TXT Format (Plain Text)

**Verwendung:** Einfaches Lesen, Terminal, Email

**Struktur:**
```
================================================================================
Chat Export Title
Exported: 2026-02-08 10:00:00
================================================================================

[1] USER - 2026-02-08 09:00:00
--------------------------------------------------------------------------------
Nachricht Inhalt...

[2] ASSISTANT - 2026-02-08 09:01:15
--------------------------------------------------------------------------------
Antwort Inhalt...
```

### 2. Markdown Format (.md)

**Verwendung:** GitHub, Notion, Obsidian, Web

**Struktur:**
```markdown
# Chat Export Title

**Exported:** 2026-02-08 10:00:00

---

## [1] User - 2026-02-08 09:00:00

Nachricht Inhalt...

---

## [2] Assistant - 2026-02-08 09:01:15

Antwort Inhalt...
```

### 3. Word-Ready Format (.md → .docx)

**Verwendung:** Microsoft Word, Professional Docs

**Features:**
- Title Page mit Metadata
- Table of Contents
- Numbered Messages
- Page Breaks

**Konvertierung zu DOCX:**
```bash
# Mit pandoc (empfohlen)
pandoc exports/chat_export_2026-02-08_word.md -o exports/chat_export.docx

# Mit pandoc + Template
pandoc exports/chat_export_2026-02-08_word.md -o exports/chat_export.docx --reference-doc=template.docx
```

## 🔧 Input-Formate

### 1. ChatGPT JSON Export

**Official Export:**
- Settings → Data controls → Export data
- Format: `conversations.json`

**Struktur:**
```json
{
  "mapping": {
    "node_id": {
      "message": {
        "author": {"role": "user"},
        "content": {"parts": ["Message text"]},
        "create_time": 1707390000
      }
    }
  }
}
```

### 2. Simple Text Format

**Format:**
```
[USER]
Erste Nachricht
[/USER]

[ASSISTANT]
Antwort darauf
[/ASSISTANT]
```

## 🛠️ Installation Zusätzlicher Tools

### Pandoc für Word-Export

**macOS:**
```bash
brew install pandoc
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install pandoc
```

**Windows:**
```powershell
choco install pandoc
```

### Python Dependencies

```bash
# Keine zusätzlichen Dependencies nötig!
# Verwendet nur Standard-Library
python3 chat_export_tool.py --example
```

## 📁 Verzeichnis-Struktur

```
ai-empire/
├── chat_export_tool.py          # Haupt-Tool
├── exports/                      # Output-Verzeichnis
│   ├── chat_export_*.txt
│   ├── chat_export_*.md
│   └── chat_export_*_word.md
└── docs/
    └── CHAT_EXPORT_GUIDE.md     # Diese Dokumentation
```

## 💡 Use Cases

### 1. Documentation von AI-Projekten

```bash
# ChatGPT Session über OpenClaw Implementation
python3 chat_export_tool.py openclaw_session.json -t "OpenClaw Setup Session"

# → Speichern in gold-nuggets/
mv exports/chat_export_*.md gold-nuggets/GOLD_OPENCLAW_SESSION.md
```

### 2. Team Collaboration

```bash
# Export für Team-Meeting
python3 chat_export_tool.py team_discussion.json -f word -t "AI Empire Team Meeting"

# → Konvertieren zu Word
pandoc exports/*.md -o team_meeting.docx

# → Teilen via Email/Slack
```

### 3. Knowledge Base

```bash
# Mehrere Sessions exportieren
for file in sessions/*.json; do
  python3 chat_export_tool.py "$file" -f md
done

# → Alle Markdown Files in Obsidian/Notion importieren
```

### 4. Backup & Archive

```bash
# Vollständiges Backup
python3 chat_export_tool.py all_conversations.json -t "Maurice AI Empire - Full Archive"

# → Komprimieren
cd exports
zip -r ../ai_empire_chats_$(date +%Y%m%d).zip *.md *.txt
```

## 🎯 Best Practices

### 1. Naming Convention

```bash
# Mit Datum und Projekt
python3 chat_export_tool.py input.json -t "2026-02-08 OpenClaw Implementation"

# Mit Kategorie
python3 chat_export_tool.py input.json -t "[BMA] Brandmeldeanlagen AI Integration"

# Mit Session ID
python3 chat_export_tool.py input.json -t "Session #42 - Revenue Optimization"
```

### 2. Organisation

```
exports/
├── 2026-02/                    # Monat
│   ├── 08-openclaw/           # Tag + Projekt
│   │   ├── session_morning.md
│   │   └── session_evening.md
│   └── 09-bma/
│       └── bma_discussion.md
└── archive/                    # Alte Exports
    └── 2026-01/
```

### 3. Integration in Workflows

```bash
# Git Commit Hook
git add exports/*.md
git commit -m "docs: Add chat export from $(date +%Y-%m-%d)"

# Cron Job für automatisches Backup
0 0 * * * cd /path/to/ai-empire && python3 chat_export_tool.py --example
```

## 🔍 Troubleshooting

### Problem: "No messages found"

**Lösung:**
```bash
# Check JSON structure
cat input.json | jq '.mapping | length'

# Try simple format
cat input.txt | head -20
```

### Problem: "File not found"

**Lösung:**
```bash
# Check path
ls -la input.json

# Use absolute path
python3 chat_export_tool.py /absolute/path/to/input.json
```

### Problem: Encoding Errors

**Lösung:**
```bash
# Check file encoding
file -i input.txt

# Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.txt > input_utf8.txt
```

## 📊 Performance

| Input Size | Messages | Export Time | Output Size |
|------------|----------|-------------|-------------|
| 100 KB | ~50 | < 1s | 150 KB |
| 1 MB | ~500 | ~2s | 1.5 MB |
| 10 MB | ~5000 | ~10s | 15 MB |

## 🔐 Privacy & Security

- ✅ Alle Exports bleiben lokal
- ✅ Keine Cloud-Uploads
- ✅ Keine API-Calls
- ✅ Pure Python Standard Library

**Empfehlung für sensitive Daten:**
```bash
# Export in /tmp (wird beim Reboot gelöscht)
python3 chat_export_tool.py input.json -o /tmp/exports

# Mit Verschlüsselung
python3 chat_export_tool.py input.json
cd exports
zip -e -r encrypted_export.zip *.md  # Passwort-geschützt
```

## 🚀 Advanced Usage

### 1. Batch Processing

```bash
#!/bin/bash
# batch_export.sh

for json_file in raw_exports/*.json; do
  filename=$(basename "$json_file" .json)
  python3 chat_export_tool.py "$json_file" -t "Session: $filename" -o "exports/$filename"
done
```

### 2. Custom Parser

```python
# custom_parser.py
from chat_export_tool import ChatExporter

exporter = ChatExporter()

# Custom message format
messages = [
    {'role': 'user', 'content': 'Hello', 'timestamp': '2026-02-08 10:00:00'},
    {'role': 'assistant', 'content': 'Hi!', 'timestamp': '2026-02-08 10:00:15'}
]

# Export
exporter.export_to_markdown(messages, title="Custom Chat")
```

### 3. Integration mit GitHub Actions

```yaml
# .github/workflows/chat-export.yml
name: Auto Chat Export
on:
  push:
    paths:
      - 'raw_chats/*.json'

jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Export Chats
        run: |
          python3 chat_export_tool.py raw_chats/*.json
          git add exports/
          git commit -m "Auto-export: $(date)"
          git push
```

## 📚 Weiterführende Links

- [ChatGPT Data Export](https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data)
- [Pandoc Documentation](https://pandoc.org/MANUAL.html)
- [Markdown Guide](https://www.markdownguide.org/)

## 🆘 Support

Bei Fragen oder Problemen:

1. Check diese Dokumentation
2. Run `python3 chat_export_tool.py --help`
3. Generate example: `python3 chat_export_tool.py --example`
4. Create GitHub Issue: `@mauricepfeifer-ctrl/AIEmpire-Core`

---

**Version:** 1.0.0  
**Author:** Maurice  
**Last Updated:** 2026-02-08
