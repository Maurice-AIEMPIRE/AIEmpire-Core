# GOLD NUGGET: NotebookLM + OpenClaw Workflow

**Datum:** 2026-02-08
**Quelle:** Julian Goldie (@JulianGoldieSEO), Google Docs, GitHub, Community Research
**Bewertung:** HOCHRELEVANT - Direkter Fit fuer Maurice's AI Empire

---

## 1. Was ist Google NotebookLM?

Google NotebookLM ist ein KI-gestuetzter Research-Assistent, der auf Gemini basiert und NUR aus hochgeladenen Quellen antwortet (Zero Hallucination by Design).

### Core Features:
- **Source-Grounded AI:** Antwortet ausschliesslich basierend auf hochgeladenen Dokumenten (PDFs, Google Docs, YouTube URLs, Webseiten, Slides)
- **Audio Overviews:** Generiert Podcast-artige Audio-Zusammenfassungen aus deinen Quellen
- **Video Overviews (NEU 2025/2026):** Generiert KI-erzaehlte Video-Zusammenfassungen mit Slides, Diagrammen, Zitaten - powered by "Nano Banana Pro" Model
- **Deep Research Mode:** Autonomer Agent der komplexe Fragen in Sub-Fragen zerlegt und 10-20 Min. das Web durchsucht
- **Fast Research Mode:** Schnelle Web-Recherche fuer Quick Pulls
- **Studio Panel:** Generiert Videos, Infografiken, Praesentationen, Datentabellen, Audio
- **35+ Sprachen, 180+ Regionen**

### Video Overview Formate:
- **Explainer:** Strukturiertes, umfassendes Video fuer tiefes Verstaendnis
- **Brief:** Bite-sized Video fuer schnelles Core-Verstaendnis
- **Visuelle Stile:** Classic, Whiteboard, Watercolor, Retro Print, Heritage, Paper-craft, Kawaii, Anime

### Zugang:
- **Consumer:** Kostenlos unter notebooklm.google.com - KEINE API
- **Enterprise:** NotebookLM Enterprise API (Pre-GA/Alpha) via Google Cloud
- **Education:** Verfuegbar fuer alle Education-User seit August 2025

---

## 2. NotebookLM API Status

### Offizielle API (Enterprise Only):
- **NotebookLM Enterprise API** - Pre-GA/Alpha Status
- Endpunkte: US (`us-`), Europe (`eu-`), Global (`global-`)
- Operationen: `notebooks.create`, `notebooks.get`, `notebooks.listRecentlyViewed`
- Quellen hinzufuegen: Web-URLs, YouTube, Google Drive, Raw Text
- Erfordert Google Cloud Setup + Authentication

### Inoffizielle Tools:
1. **notebooklm-py** (Python): Voller programmatischer Zugang inkl. Features die das Web-UI nicht hat
2. **nblm-rs** (Rust): Enterprise API Client mit CLI + Python SDK
3. **AutoContent API** (Commercial): Cloud-basierte Automation fuer NotebookLM-aehnliche Features
4. **Apify Integration:** Export zu JSON, CSV, Markdown, Excel
5. **Open Notebook** (Open Source): Eigene Implementation mit REST API

### WICHTIG: Consumer NotebookLM hat KEINE Automation-Features - rein manuell.

---

## 3. NotebookLM MCP Server (GAME CHANGER)

Es existieren bereits mehrere MCP Server die NotebookLM fuer AI Agents zugaenglich machen:

### Top 3 MCP Implementierungen:

#### a) PleasePrompto/notebooklm-mcp
- Setup: `claude mcp add notebooklm npx notebooklm-mcp@latest`
- Funktioniert mit: Claude Code, Codex, Cursor
- Persistent Auth, Library Management, Cross-Client Sharing
- Zero Hallucination - antwortet nur aus deiner Knowledge Base

#### b) roomi-fields/notebooklm-mcp
- REST API + MCP Server
- **v1.5.0:** Komplette Studio Content Generation (Video, Infographic, Presentation, Data Table)
- Notes Management, Source Deletion
- Docker Deployment (auch NAS: Synology, QNAP)
- Perfekt fuer n8n Workflows

#### c) jacob-bd/notebooklm-mcp-cli
- Unified Package: CLI (`nlm`) + MCP Server (`notebooklm-mcp`)
- Create Notebooks, Add Sources, Run Research, Sync Drive, Generate Studio Artifacts
- Auth: Auto-Mode (Chrome Login), Manual (Cookies), Named Profiles
- Nutzt undokumentierte interne NotebookLM APIs

### Architektur-Flow:
```
Dein Task -> Claude/Codex -> MCP Server -> Chrome Automation -> NotebookLM -> Gemini 2.5 -> Deine Docs -> Zurueck
```

### WARNUNG:
- Nutzt undokumentierte APIs (koennen sich aendern)
- Google koennte automatisierte Nutzung erkennen
- Empfehlung: Dediziertes Google-Konto verwenden

---

## 4. Julian Goldie's Workflow (Der Tweet)

Julian Goldie (@JulianGoldieSEO) beschreibt mehrere Workflows:

### A) NotebookLM + Antigravity Workflow:
```
NotebookLM (Strategist) -> Antigravity (Builder)
Research & Plan         -> Execute & Build
```
- NotebookLM liest, organisiert, plant
- Antigravity (Google's AI-Workspace) fuehrt aus, schreibt Code
- Closed Feedback Loop: Text -> Technology

### B) 6-in-1 Content Multiplier System:
```
1 Idee -> NotebookLM Research -> Gemini Processing -> 6 Formate:
  1. Video
  2. Blog Post
  3. Tweet
  4. Email
  5. Thread
  6. Social Post
```

### C) NotebookLM + OpenClaw Integration:
- Julian hat einen OpenClaw Setup Guide veroeffentlicht
- NotebookLM Skill fuer OpenClaw existiert: "Analyze your local files with Google NotebookLM's AI"
- Julian beschreibt auch Ollama + Kimi K2.5 -> OpenClaw Pipeline
- Claw Tasks AI: Autonome Agenten fuehren Tasks aus (wie ein "Fiverr fuer AI Agents")

### D) Der beschriebene Workflow:
```
1. NotebookLM researches the topic (Deep Research Mode)
2. Builds structure + gaps from real data (Source-Grounded)
3. Generates video summaries automatically (Studio Video Overview)
4. OpenClaw executes (Autonomous Agent Execution)
```

### Julian's 3-Step Framework:
1. **Source:** Beste Materialien in NotebookLM hochladen
2. **Build:** Google Antigravity verbindet Materialien mit Workspace-Tools
3. **Execute:** OpenClaw/Agents fuehren den Plan autonom aus

---

## 5. Integration in Maurice's AI Empire

### Direkter Fit:
```
Maurice's Stack:
  Ollama (Local, Free)     = Execution Layer
  Kimi K2.5 (Cloud, Cheap) = Decomposition Layer
  + NotebookLM (Free/Cloud) = Research & Structure Layer  <-- NEU!
  + OpenClaw (Local)         = Agent Orchestration Layer   <-- NEU!
```

### Konkreter Integration-Plan:

#### Phase 1: NotebookLM MCP Server aufsetzen
```bash
# Option A: Via Claude Code
claude mcp add notebooklm npx notebooklm-mcp@latest

# Option B: Via CLI Tool
pip install notebooklm-mcp-cli
nlm auth login  # Browser-basierte Auth
```

#### Phase 2: NotebookLM als Research-Layer
- BMA-Expertise Dokumente hochladen (Brandmeldeanlagen)
- Normen, Richtlinien, technische Docs als Sources
- Deep Research fuer neue Themen/Maerkte

#### Phase 3: Video/Content Pipeline
```
NotebookLM Deep Research
    -> Video Overview generieren (automatisch)
    -> Audio Overview generieren (Podcast)
    -> Infografiken generieren
    -> Content via Kimi/Ollama weiterverarbeiten
    -> OpenClaw Agents verteilen an Plattformen
```

#### Phase 4: Vollautomatisierung
```
Event Broker empfaengt Research-Auftrag
    -> NotebookLM MCP: Research + Structure
    -> Kimi K2.5: Task Decomposition
    -> Ollama: Content Execution (FREE)
    -> OpenClaw: Distribution + Monitoring
```

---

## 6. Monetarisierung

### Sofortige Opportunities:

#### A) BMA Content Factory
- BMA-Wissen in NotebookLM laden
- Video Overviews fuer Schulungen generieren
- Verkauf als Online-Kurs oder Schulungspaket
- Zielgruppe: Elektriker, Brandschutzbeauftragte, Facility Manager
- **Potenzial: 50-200 EUR/Monat pro Abo**

#### B) AI Research-as-a-Service
- NotebookLM + OpenClaw als automatisierten Research-Service anbieten
- Kunden liefern Thema -> System liefert strukturierte Reports + Videos
- **Potenzial: 500-5000 EUR pro Research-Auftrag**

#### C) Content Multiplier Service
- 1 Input -> 6 Formate (Julian Goldie's Modell)
- Fuer Unternehmen die Content brauchen
- Vollautomatisiert mit Maurice's Stack
- **Potenzial: 2000-10000 EUR/Monat**

#### D) Claw Tasks Marketplace
- AI Agents auf dem Claw Tasks Marketplace anbieten
- Spezialisierte BMA/Safety Agents
- **Potenzial: Passives Einkommen**

#### E) NotebookLM + OpenClaw Setup Service
- Anderen beibringen wie man das System aufsetzt
- Skool Community (wie Julian Goldie mit 46.000+ Members)
- **Potenzial: 47-97 EUR/Monat Membership**

---

## 7. Konkrete Next Steps

### SOFORT (Diese Woche):
- [ ] Dediziertes Google-Konto fuer NotebookLM Automation erstellen
- [ ] `notebooklm-mcp-cli` installieren und testen
- [ ] Ersten Test: BMA-Dokument hochladen, Video Overview generieren
- [ ] Julian Goldie's Skool Community joinen (kostenlos) fuer Updates

### KURZFRISTIG (Naechste 2 Wochen):
- [ ] NotebookLM MCP Server in Claude Code integrieren
- [ ] OpenClaw Skill fuer NotebookLM testen
- [ ] Erste automatisierte Research-Pipeline bauen
- [ ] Video Overview Quality testen fuer BMA-Content

### MITTELFRISTIG (1 Monat):
- [ ] Voll-automatisierte Content Pipeline: Research -> Video -> Distribution
- [ ] BMA Online-Kurs MVP mit NotebookLM-generierten Videos
- [ ] Claw Tasks Marketplace evaluieren fuer passive Income
- [ ] Event Broker Integration: NotebookLM als Research-Layer einbinden

### LANGFRISTIG (3 Monate):
- [ ] AI Research-as-a-Service launchen
- [ ] Content Multiplier Service fuer B2B Kunden
- [ ] Eigene Skool/Community fuer AI + BMA Nische
- [ ] NotebookLM Enterprise API Migration wenn GA

---

## 8. Risiken & Caveats

1. **Inoffizielle APIs:** NotebookLM MCP Server nutzen undokumentierte APIs - koennen jederzeit brechen
2. **Google Detection:** Automatisierte Nutzung koennte erkannt/geblockt werden
3. **Enterprise API Pre-GA:** Noch nicht stabil, Features koennen sich aendern
4. **OpenClaw Instabilitaet:** Projekt ist jung, Naming-Aenderungen (Clawdbot -> Moltbot -> OpenClaw)
5. **Dependency Risk:** Abhaengigkeit von Google's Free Tier fuer NotebookLM

### Mitigation:
- Dediziertes Google-Konto
- Open Notebook (Open Source Alternative) als Backup
- NotebookLM Enterprise API evaluieren wenn Budget vorhanden
- Lokale Backups aller Notebooks/Sources

---

## 9. Key Links & Ressourcen

- NotebookLM: https://notebooklm.google.com
- NotebookLM Enterprise API Docs: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks
- notebooklm-mcp (MCP Server): https://github.com/PleasePrompto/notebooklm-mcp
- notebooklm-mcp-cli: https://github.com/jacob-bd/notebooklm-mcp-cli
- notebooklm-py (Python): https://github.com/teng-lin/notebooklm-py
- Open Notebook (OSS Alternative): https://github.com/lfnovo/open-notebook
- Julian Goldie NotebookLM Tutorial: https://juliangoldie.com/google-notebooklm-tutorial/
- Julian Goldie Antigravity Workflow: https://juliangoldie.com/notebooklm-and-antigravity-workflow/
- Julian Goldie OpenClaw Setup: https://juliangoldie.com/openclaw-setup/
- Julian Goldie MCP Setup: https://juliangoldie.com/notebooklm-mcp-setup/
- OpenClaw Docs: https://docs.openclaw.ai/tools
- OpenClaw GitHub Discussion #8011: https://github.com/openclaw/openclaw/discussions/8011

---

**FAZIT:** NotebookLM + OpenClaw ist ein extrem maechtiger Stack. NotebookLM liefert source-grounded Research ohne Halluzinationen, generiert automatisch Videos/Audio/Infografiken, und ueber MCP Server ist das Ganze programmatisch steuerbar. Combined mit Maurice's bestehendem Ollama + Kimi Stack entsteht eine vollstaendig automatisierte Research-to-Content-to-Distribution Pipeline. Die MCP Integration ist JETZT verfuegbar und testbar.
