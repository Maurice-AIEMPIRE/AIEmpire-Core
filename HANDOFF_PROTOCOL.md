# HANDOFF PROTOCOL: Claude Code ↔ GitHub Copilot
# Automatischer Uebergang wenn Claude ausfaellt

## SO FUNKTIONIERT ES

### Wenn Claude Code AKTIV ist:
1. Claude arbeitet lokal auf deinem Mac
2. Pushed Updates automatisch auf GitHub
3. Gold Nuggets, System Status, Tasks → alles auf GitHub

### Wenn Claude Code AUSFAELLT:
1. Oeffne GitHub Copilot Chat
2. Sage: "Lies HANDOFF_PROTOCOL.md und COPILOT_BRIEFING.md im Repo AIEmpire-Core"
3. Copilot hat ALLES was er braucht:
   - System-Status in docs/OPENCLAW_SYSTEM_STATUS.md
   - Alle Tasks in docs/CHATGPT_TASKS.md
   - Gold Nuggets in gold-nuggets/
   - Architektur in docs/SYSTEM_ARCHITECTURE.md
   - Config Backup in openclaw-config/

### Standard-Befehle fuer Copilot:

```
"Was ist der aktuelle Status?"
→ Lies docs/OPENCLAW_SYSTEM_STATUS.md

"Was muss ich als naechstes tun?"
→ Lies docs/CHATGPT_TASKS.md + COPILOT_BRIEFING.md

"Erstelle Content/Posts"
→ Nutze x-lead-machine/ Templates

"Zeig mir die Architektur"
→ Lies docs/SYSTEM_ARCHITECTURE.md

"Was haben wir schon verdient?"
→ Lies gold-nuggets/MONETIZATION_REPORT_2026-02-08.md
```

---

## COPILOT QUICKSTART (Copy-Paste in Copilot Chat)

```
Du bist der AI-Assistent fuer Maurice's AI Empire.
Repo: mauricepfeifer-ctrl/AIEmpire-Core

REGELN:
1. Keine Rueckfragen - einfach machen
2. Deutsch fuer Maurice, Englisch fuer Code
3. Immer pragmatisch und schnell
4. Revenue first - alles muss Geld bringen

KONTEXT:
- Maurice: 37J, Elektrotechnikmeister, 16J BMA-Expertise
- Ziel: 100 Mio EUR in 1-3 Jahren
- Tech: OpenClaw + Ollama + Kimi + Redis + PostgreSQL
- Revenue: EUR 0 bisher → EUR 50-100 overnight Target

LIES ZUERST:
1. COPILOT_BRIEFING.md
2. docs/SYSTEM_ARCHITECTURE.md
3. docs/CHATGPT_TASKS.md
4. gold-nuggets/GOLD_OPENCLAW_MASTERPLAN_2026-02-08.md

DANN: Fuehre die Tasks aus!
```

---

## SYNC PROTOKOLL

### Claude → GitHub (automatisch bei jeder Session)
- [ ] CURRENT_STATUS.md updaten
- [ ] Neue Gold Nuggets pushen
- [ ] Task-Liste aktualisieren
- [ ] Code-Aenderungen committen

### GitHub → Claude (bei Session-Start)
- [ ] Letzte Copilot-Commits lesen
- [ ] Issue Tracker checken
- [ ] PR Reviews verarbeiten

### Copilot → GitHub (automatisch)
- [ ] Code generieren → PR erstellen
- [ ] Tasks abarbeiten → Issues schliessen
- [ ] Status Updates → Commit Messages

---

## EMERGENCY COMMANDS

Falls alles schiefgeht:
```bash
# System neu starten
brew services restart redis
brew services restart postgresql@16
ollama serve &
openclaw gateway start

# Status checken
openclaw status
ollama list
redis-cli ping
```
