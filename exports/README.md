# Chat Exports

Dieses Verzeichnis enthält exportierte Chat-Konversationen in verschiedenen Formaten.

## 📁 Struktur

```
exports/
├── README.md                           # Diese Datei
├── chat_export_YYYY-MM-DD_HH-MM-SS.txt  # Plain Text Format
├── chat_export_YYYY-MM-DD_HH-MM-SS.md   # Markdown Format
└── chat_export_YYYY-MM-DD_HH-MM-SS_word.md  # Word-Ready Format
```

## 🚀 Quick Start

```bash
# Beispiel-Export generieren
cd /home/runner/work/AIEmpire-Core/AIEmpire-Core
python3 chat_export_tool.py --example

# Eigenen Chat exportieren
python3 chat_export_tool.py your_chat.json -t "Mein Chat Titel"
```

## 📖 Vollständige Dokumentation

Siehe: [docs/CHAT_EXPORT_GUIDE.md](../docs/CHAT_EXPORT_GUIDE.md)

## 🗑️ Cleanup

Alte Exports können gelöscht werden:

```bash
# Alle älter als 30 Tage
find exports/ -name "chat_export_*.txt" -mtime +30 -delete
find exports/ -name "chat_export_*.md" -mtime +30 -delete
```

## 🔒 .gitignore

Die Exports werden nicht automatisch committed. Um spezifische Exports zu teilen:

```bash
git add exports/wichtiger_export.md
git commit -m "docs: Add important chat export"
```
