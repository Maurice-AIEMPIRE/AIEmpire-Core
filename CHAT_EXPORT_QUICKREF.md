# Chat Export Tool - Quick Reference

## 🚀 One-Line Commands

```bash
# Generate example
python3 chat_export_tool.py --example

# Export ChatGPT JSON
python3 chat_export_tool.py conversations.json

# Export with custom title
python3 chat_export_tool.py input.json -t "My Session"

# Only Markdown
python3 chat_export_tool.py input.json -f md

# Custom output directory
python3 chat_export_tool.py input.json -o /tmp/my-exports
```

## 📋 Supported Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| Plain Text | `.txt` | Reading, Email |
| Markdown | `.md` | GitHub, Notion |
| Word-Ready | `_word.md` | MS Word (via pandoc) |

## 🔄 Convert to Word

```bash
# Install pandoc first
brew install pandoc  # macOS
apt-get install pandoc  # Linux

# Convert
pandoc exports/chat_export_*_word.md -o output.docx
```

## 📖 Full Documentation

See [docs/CHAT_EXPORT_GUIDE.md](docs/CHAT_EXPORT_GUIDE.md) for complete guide.

## 💡 Common Use Cases

### 1. Document AI Sessions
```bash
python3 chat_export_tool.py openclaw_session.json -t "OpenClaw Setup"
mv exports/chat_export_*.md gold-nuggets/GOLD_OPENCLAW_SESSION.md
```

### 2. Share with Team
```bash
python3 chat_export_tool.py team_chat.json -f word -t "Team Meeting"
pandoc exports/*_word.md -o team_meeting.docx
```

### 3. Backup All Chats
```bash
for file in *.json; do
  python3 chat_export_tool.py "$file"
done
```

## 🆘 Need Help?

```bash
python3 chat_export_tool.py --help
```

---

**Version:** 1.0.0 | **Author:** Maurice
