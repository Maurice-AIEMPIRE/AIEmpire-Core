# 🏷️ Label System

GitHub Labels für Routing, Priorisierung und Tracking.

## Kategorien

### Typ-Labels (Routing)

| Label | Farbe | Beschreibung |
|-------|-------|--------------|
| `research` | 🔵 `#0075ca` | Recherche-Aufgabe |
| `code` | 🟢 `#0e8a16` | Code-Änderung |
| `docs` | 🟣 `#5319e7` | Dokumentation |
| `ops` | 🟠 `#d93f0b` | Infrastruktur / DevOps |
| `security` | 🔴 `#b60205` | Sicherheit |
| `growth` | 🟡 `#fbca04` | Wachstum / Marketing |
| `revenue` | 💰 `#0e8a16` | Einnahmen-bezogen |

### Prioritäts-Labels

| Label | Farbe | Beschreibung |
|-------|-------|--------------|
| `P0` | 🔴 `#b60205` | Kritisch – sofort |
| `P1` | 🟠 `#d93f0b` | Hoch – diese Woche |
| `P2` | 🟡 `#fbca04` | Normal – wenn Zeit |

### Status-Labels

| Label | Farbe | Beschreibung |
|-------|-------|--------------|
| `atomic-task` | ⚛️ `#1d76db` | Atomic Task für Agenten |
| `bug` | 🐛 `#d73a4a` | Fehlerbericht |
| `feature` | ✨ `#a2eeef` | Neue Funktion |
| `claude-failover` | 🔄 `#e4e669` | Claude API Failover |
| `automation` | 🤖 `#bfd4f2` | Automatisierung |

### Agent-Labels (Modell-Routing)

| Label | Beschreibung |
|-------|--------------|
| `agent:claude` | Aufgabe für Claude |
| `agent:kimi` | Aufgabe für Kimi |
| `agent:ollama` | Aufgabe für lokales LLM |
| `agent:chatgpt` | Aufgabe für ChatGPT |

## Verwendung

Labels bestimmen:
1. **Wer** arbeitet (Agent-Routing)
2. **Wie dringend** (Priorität)
3. **Was** gemacht wird (Typ)

Der Issue Command Bot kann Labels automatisch setzen basierend auf Inhalt.
