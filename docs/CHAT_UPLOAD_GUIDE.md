# Chat Upload & Multi-Model Support Guide

> Lade Chat-Verläufe hoch und stelle Fragen mit allen verfügbaren AI-Modellen

## 🎯 Überblick

Das Chat-Upload-System ermöglicht:
1. ✅ **Chat-Upload** - Lade bestehende Chat-Verläufe hoch
2. ✅ **Multi-Model Support** - Nutze Claude, Kimi, oder Ollama (lokal)
3. ✅ **Kontext-Bewusstsein** - Fragen mit voller Chat-Historie
4. ✅ **Model-Wechsel** - Wechsle flexibel zwischen Modellen
5. ✅ **Export/Import** - Exportiere und importiere Chats

---

## 🚀 Quick Start

### 1. Verfügbare Modelle anzeigen

In einem GitHub Issue oder Comment:

```
@bot models
```

Das System zeigt alle verfügbaren Modelle:
- **Claude 3 Haiku, Sonnet, Opus** (wenn ANTHROPIC_API_KEY gesetzt)
- **Kimi (Moonshot)** (wenn MOONSHOT_API_KEY gesetzt)
- **Ollama Modelle** (Qwen 2.5 Coder, Mistral) - Lokal, kostenlos!

### 2. Chat hochladen

Lade einen bestehenden Chat-Verlauf hoch:

```
@bot upload-chat text
User: Hello, wie kann ich dir helfen?
Assistant: Hallo! Ich bin bereit zu helfen.
User: Ich möchte mehr über AI lernen.
Assistant: Sehr gerne! AI steht für Artificial Intelligence...
```

Unterstützte Formate:
- `text` - Einfacher Text mit "User:" und "Assistant:" Labels
- `json` - JSON Array mit message objects
- `markdown` - Markdown mit ## Headers

### 3. Fragen stellen

Stelle eine Frage mit dem aktuellen Modell:

```
@bot ask Was ist AI Automation?
```

Mit spezifischem Modell:

```
@bot ask:claude-sonnet Erkläre mir Machine Learning.
```

### 4. Modell wechseln

Wechsle zu einem anderen Modell:

```
@bot switch-model ollama-qwen
```

---

## 📋 Alle Commands

### Chat Upload & Management

#### `@bot upload-chat [format]`
Lade Chat-Historie hoch.

**Beispiel - Text Format:**
```
@bot upload-chat text
User: Hallo
Assistant: Hi! Wie kann ich helfen?
User: Was ist Python?
Assistant: Python ist eine Programmiersprache...
```

**Beispiel - JSON Format:**
```
@bot upload-chat json
[
  {"role": "user", "content": "Hallo"},
  {"role": "assistant", "content": "Hi! Wie kann ich helfen?"}
]
```

**Beispiel - Markdown Format:**
```
@bot upload-chat markdown
## User
Hallo

## Assistant
Hi! Wie kann ich helfen?

## User
Was ist Python?
```

#### `@bot ask [question]`
Stelle eine Frage mit Kontext.

**Beispiel:**
```
@bot ask Erkläre AI Automation in einfachen Worten.
```

**Mit spezifischem Modell:**
```
@bot ask:claude-opus Schreibe einen ausführlichen Artikel über AI.
```

#### `@bot export-chat`
Exportiere die aktuelle Konversation als JSON.

```
@bot export-chat
```

#### `@bot clear-history`
Lösche die Chat-Historie.

```
@bot clear-history
```

### Model Management

#### `@bot models`
Liste alle verfügbaren Modelle.

```
@bot models
```

#### `@bot switch-model [name]`
Wechsle zu einem anderen Modell.

**Beispiele:**
```
@bot switch-model claude-sonnet
@bot switch-model kimi
@bot switch-model ollama-qwen
```

---

## 🤖 Verfügbare Modelle

### Cloud Modelle (API Keys erforderlich)

#### Claude 3 Familie (Anthropic)
- **claude** - Claude 3 Haiku (Schnell, günstig)
- **claude-sonnet** - Claude 3 Sonnet (Balanced)
- **claude-opus** - Claude 3 Opus (Beste Qualität)

**API Key:** `ANTHROPIC_API_KEY`

#### Kimi / Moonshot
- **kimi** - Moonshot v1-8k (Sehr günstig, 8K context)

**API Key:** `MOONSHOT_API_KEY`

### Lokale Modelle (Ollama)

#### Ollama Modelle (Kostenlos!)
- **ollama-qwen** - Qwen 2.5 Coder 7B (Code-spezialisiert)
- **ollama-mistral** - Mistral 7B (Allgemein)

**Voraussetzung:** Ollama muss laufen auf `http://localhost:11434`

---

## 💡 Use Cases

### Use Case 1: Chat von Mac zu GitHub übertragen

Du hast einen langen Chat auf dem Mac mit Ollama geführt und willst ihn auf GitHub fortsetzen:

1. **Exportiere Chat vom Mac:**
   ```bash
   # Speichere deinen Chat in eine Datei
   cat > chat_export.txt << EOF
   User: Hello
   Assistant: Hi there!
   ...
   EOF
   ```

2. **In GitHub Issue:**
   ```
   @bot upload-chat text
   User: Hello
   Assistant: Hi there!
   ...
   ```

3. **Weiter chatten:**
   ```
   @bot ask Kannst du mir das nochmal zusammenfassen?
   ```

### Use Case 2: Modell-Vergleich

Teste verschiedene Modelle mit der gleichen Frage:

```
@bot switch-model kimi
@bot ask Was ist Machine Learning?

@bot switch-model claude-sonnet
@bot ask Was ist Machine Learning?

@bot switch-model ollama-qwen
@bot ask Was ist Machine Learning?
```

### Use Case 3: Kosten-Optimierung

Nutze Ollama (kostenlos) für einfache Fragen, Claude für komplexe:

```
# Einfache Frage - Ollama (kostenlos)
@bot switch-model ollama-qwen
@bot ask Was ist Python?

# Komplexe Aufgabe - Claude Opus (beste Qualität)
@bot switch-model claude-opus
@bot ask Schreibe eine komplette API-Dokumentation...
```

### Use Case 4: Konversations-Export

Exportiere wichtige Chats für Dokumentation:

```
@bot export-chat
```

Kopiere die JSON-Ausgabe und speichere sie.

---

## 🔧 Setup & Configuration

### 1. API Keys einrichten

In GitHub Repo Settings → Secrets and Variables → Actions:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
MOONSHOT_API_KEY=sk-your-moonshot-key
```

### 2. Ollama lokal installieren (Optional)

Auf Mac:
```bash
brew install ollama
ollama serve  # Startet Server auf Port 11434
ollama pull qwen2.5-coder:7b
ollama pull mistral:7b
```

### 3. Workflow aktivieren

Der Chat Manager ist bereits integriert in:
- `github_control_interface.py`
- `chat_manager.py`

---

## 📊 Model Comparison

| Model | API | Cost | Speed | Quality | Best For |
|-------|-----|------|-------|---------|----------|
| Ollama Qwen | Local | FREE | Fast | Good | Code, Development |
| Ollama Mistral | Local | FREE | Fast | Good | General Tasks |
| Kimi | Moonshot | Very Low | Fast | Good | Bulk Tasks |
| Claude Haiku | Anthropic | Low | Very Fast | Good | Quick Questions |
| Claude Sonnet | Anthropic | Medium | Fast | Excellent | Most Tasks |
| Claude Opus | Anthropic | High | Medium | Best | Complex Work |

---

## 🎓 Tipps & Best Practices

### Model-Wahl
1. **Ollama (lokal)** für alles was möglich ist → Spart Geld
2. **Kimi** für Bulk-Tasks → Sehr günstig
3. **Claude Haiku** für schnelle Antworten → Günstig
4. **Claude Sonnet** für wichtige Aufgaben → Balanced
5. **Claude Opus** nur für kritische/komplexe Tasks → Teuer

### Chat Upload
1. Nutze `text` format für einfache Konversationen
2. Nutze `json` format für strukturierte Daten
3. Nutze `markdown` format für formatierte Chats

### Kontext Management
1. Lade nur relevante Chat-Historie hoch
2. Nutze `@bot clear-history` zwischen verschiedenen Themen
3. Exportiere wichtige Chats regelmäßig

---

## 🚨 Troubleshooting

### Problem: Model nicht verfügbar

**Lösung:**
```
@bot models
```
Prüfe welche Modelle verfügbar sind und ob API Keys gesetzt sind.

### Problem: Ollama Fehler

**Lösung:**
1. Prüfe ob Ollama läuft: `http://localhost:11434`
2. Starte Ollama: `ollama serve`
3. Prüfe ob Modelle installiert: `ollama list`

### Problem: API Rate Limits

**Lösung:**
Wechsle zu Ollama (lokal, kostenlos):
```
@bot switch-model ollama-qwen
```

### Problem: Chat Upload schlägt fehl

**Lösung:**
1. Prüfe Format (`text`, `json`, `markdown`)
2. Stelle sicher dass "User:" und "Assistant:" Labels korrekt sind
3. Prüfe JSON Syntax bei json format

---

## 📞 Support

**Commands für Hilfe:**
```
@bot help
@bot models
@bot status
```

**Dokumentation:**
- [GITHUB_CONTROL_SYSTEM.md](../GITHUB_CONTROL_SYSTEM.md)
- [README.md](../README.md)

---

## 🎉 Beispiel-Workflow

### Kompletter Workflow: Mac → GitHub → Multi-Model

```bash
# 1. Auf dem Mac: Chat in Datei speichern
cat > my_chat.txt << EOF
User: Ich arbeite an einem Python Projekt
Assistant: Cool! Woran arbeitest du?
User: Eine API für AI Automation
Assistant: Interessant! Was für Features brauchst du?
EOF
```

In GitHub Issue:
```
# 2. Chat hochladen
@bot upload-chat text
User: Ich arbeite an einem Python Projekt
Assistant: Cool! Woran arbeitest du?
User: Eine API für AI Automation
Assistant: Interessant! Was für Features brauchst du?

# 3. Mit Kimi weitermachen (günstig)
@bot switch-model kimi
@bot ask Welche Python Packages brauch ich für eine REST API?

# 4. Für Code-Hilfe zu Ollama wechseln (kostenlos)
@bot switch-model ollama-qwen
@bot ask Schreibe mir ein FastAPI Beispiel mit Authentication

# 5. Finale Review mit Claude (beste Qualität)
@bot switch-model claude-opus
@bot ask Review bitte meinen kompletten Code und gib detailliertes Feedback

# 6. Export für Dokumentation
@bot export-chat
```

---

**LET'S BUILD WITH ALL MODELS! 🚀🤖**
