# Chat Upload & Multi-Model - Quick Reference

> Schnellreferenz für die wichtigsten Commands

## 📋 Commands Übersicht

### Chat Management

| Command | Beschreibung | Beispiel |
|---------|--------------|----------|
| `@bot upload-chat text` | Text-Chat hochladen | `@bot upload-chat text`<br>`User: Hallo`<br>`Assistant: Hi!` |
| `@bot upload-chat json` | JSON-Chat hochladen | `@bot upload-chat json`<br>`[{"role":"user","content":"Hi"}]` |
| `@bot ask [frage]` | Frage stellen | `@bot ask Was ist AI?` |
| `@bot ask:[model] [frage]` | Mit spezifischem Modell | `@bot ask:claude-opus Schreibe Artikel` |
| `@bot export-chat` | Chat exportieren | `@bot export-chat` |
| `@bot clear-history` | Historie löschen | `@bot clear-history` |

### Model Management

| Command | Beschreibung | Beispiel |
|---------|--------------|----------|
| `@bot models` | Alle Modelle anzeigen | `@bot models` |
| `@bot switch-model [name]` | Modell wechseln | `@bot switch-model ollama-qwen` |

## 🤖 Verfügbare Modelle

| Name | API | Kosten | Verfügbarkeit |
|------|-----|--------|---------------|
| `claude` | Anthropic | $0.25/1M | ANTHROPIC_API_KEY |
| `claude-sonnet` | Anthropic | $3/1M | ANTHROPIC_API_KEY |
| `claude-opus` | Anthropic | $15/1M | ANTHROPIC_API_KEY |
| `kimi` | Moonshot | $0.0001/1K | MOONSHOT_API_KEY |
| `ollama-qwen` | Local | FREE | Ollama lokal |
| `ollama-mistral` | Local | FREE | Ollama lokal |

## 📝 Chat Formate

### Text Format
```
@bot upload-chat text
User: Erste Nachricht
Assistant: Antwort darauf
User: Nächste Frage
Assistant: Nächste Antwort
```

### JSON Format
```
@bot upload-chat json
[
  {"role": "user", "content": "Nachricht 1"},
  {"role": "assistant", "content": "Antwort 1"},
  {"role": "user", "content": "Nachricht 2"}
]
```

### Markdown Format
```
@bot upload-chat markdown
## User
Erste Nachricht

## Assistant
Antwort darauf

## User
Nächste Frage
```

## 💡 Typische Workflows

### Workflow 1: Chat vom Mac übertragen
```
# Schritt 1: Chat hochladen
@bot upload-chat text
User: [Dein Chat vom Mac]
Assistant: [Antworten vom Mac]

# Schritt 2: Weiter chatten
@bot ask Kannst du das zusammenfassen?
```

### Workflow 2: Günstig testen, dann Qualität
```
# Mit Kimi/Ollama starten (günstig/kostenlos)
@bot switch-model kimi
@bot ask Erste Ideen zu meinem Projekt?

# Für finale Version zu Claude wechseln
@bot switch-model claude-opus
@bot ask Schreibe die finale Version
```

### Workflow 3: Multi-Model Vergleich
```
@bot switch-model kimi
@bot ask [Frage]

@bot switch-model claude-sonnet
@bot ask [Gleiche Frage]

@bot switch-model ollama-qwen
@bot ask [Gleiche Frage]
```

## 🎯 Best Practices

### Kosten sparen
1. **95% mit Ollama (lokal)** → Kostenlos!
2. **4% mit Kimi** → Sehr günstig
3. **0.9% mit Claude Haiku** → Günstig
4. **0.1% mit Claude Opus** → Nur für kritische Tasks

### Modell-Wahl
- **Code/Development** → `ollama-qwen` (Qwen 2.5 Coder)
- **Allgemeine Fragen** → `kimi` oder `ollama-mistral`
- **Wichtige Tasks** → `claude-sonnet`
- **Kritische/Komplexe** → `claude-opus`

### Chat Upload
- Nutze `text` für einfache Chats
- Nutze `json` für strukturierte Daten
- Nutze `markdown` für formatierte Chats
- Exportiere wichtige Chats mit `@bot export-chat`

## 🚨 Troubleshooting

| Problem | Lösung |
|---------|--------|
| Model nicht verfügbar | `@bot models` → Check API Keys |
| Ollama Error | Ollama muss laufen: `ollama serve` |
| Rate Limits | Zu kostenlosem Ollama wechseln |
| Upload schlägt fehl | Format checken (text/json/markdown) |

## 📞 Hilfe

```
@bot help          # Alle Commands
@bot models        # Verfügbare Modelle
@bot status        # System Status
```

## 🔗 Dokumentation

- [Vollständige Anleitung](./CHAT_UPLOAD_GUIDE.md)
- [GitHub Control System](../GITHUB_CONTROL_SYSTEM.md)
- [Hauptdokumentation](../README.md)

---

**Pro-Tipp:** Nutze Ollama lokal für 95% der Tasks → Spart massiv Kosten! 💰
