# AUTOPILOT MODE — System laeuft OHNE Claude
# Stand: 2026-02-08
# Naechster Claude Reset: Sa. 11:00

---

## MAURICE — DEINE 3 SOFORT-TASKS (ohne Claude):

### TASK 1: GUMROAD FIXEN (5 min)
1. Gumroad einloggen (app.gumroad.com)
2. Products → Prompt Vault → "Content" Tab
3. PDF hochladen: ~/PROMPT_VAULT_100_Premium_KI_Prompts.pdf
4. Settings → Currency → EUR
5. Product → "Show on profile" aktivieren
6. TESTEN: Incognito → mauricepfeifer6.gumroad.com/l/luuhu → "I want this!" klicken → Pruefen ob PDF kommt

### TASK 2: X/TWITTER POSTEN (10 min)
Posts liegen fertig in: ~/.openclaw/workspace/ai-empire/04_OUTPUT/JETZT_POSTEN.md
1. Post 1 JETZT posten (copy-paste)
2. Post 4 in 2h posten
3. Post 5 in 4h posten
Jeden Post mit Reply: #KI #ChatGPT #Prompts #AITools

### TASK 3: COPILOT STARTEN (5 min)
GitHub Copilot Chat oeffnen → Sag:
"Lies CHATGPT_TASKS.md und COPILOT_BRIEFING.md im Repo AIEmpire-Core.
Fang mit Block A1 an — erstelle das Gumroad Product: OpenClaw Quick Start Guide.
KEINE RUECKFRAGEN. Einfach machen."

---

## WAS OHNE CLAUDE LAEUFT:

### GitHub Actions (24/7 automatisch)
- 08:00 DE: Content + Trends Issues generieren
- 12:00 DE: Product Issues generieren
- 18:00 DE: Lead Research + KPI Snapshot
- 00:00 DE: Deep Research Issues
- Sonntag: Weekly Review + Sprint Planning
- Bei jedem Push: Gold Nugget Index updaten

### Ollama (lokal, FREE, laeuft bereits)
- qwen2.5-coder:7b geladen (4.7 GB)
- Port 11434 aktiv
- Kann JEDERZEIT genutzt werden:
  curl http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"..."}'

### OpenClaw (laeuft als LaunchAgent)
- PID aktiv, 9 Cron Jobs konfiguriert
- Kimi K2.5 als Provider

### Brain System Orchestrator
cd ~/.openclaw/workspace/ai-empire-github/brain-system
python orchestrator.py --cycle    # Alle Gehirne starten
python orchestrator.py --health   # Health Check
python orchestrator.py --morning  # Morning Briefing
python orchestrator.py --xp 50 --action "Gumroad gefixt"

---

## WENN CLAUDE ZURUECK IST (nach Reset):

Sag einfach: "Weiter. Was hat Copilot gemacht?"
Ich lese CURRENT.md + BRAIN.md und weiss sofort Bescheid.

---

## NOTFALL-KONTAKTE (ohne Claude):

| Tool | Wie starten | Wofuer |
|------|-------------|--------|
| Ollama | Laeuft bereits | Coding, Quick Tasks |
| Kimi API | curl api.moonshot.ai/v1 | Komplexe Aufgaben |
| GitHub Copilot | GitHub Chat | Content, Code, Products |
| OpenClaw | openclaw | Automation, Skills |
| Antigravity | antigravityai.org installieren | Multi-Agent IDE (FREE!) |
