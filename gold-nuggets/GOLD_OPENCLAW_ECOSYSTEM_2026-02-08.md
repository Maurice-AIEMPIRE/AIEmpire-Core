# GOLD NUGGET: OpenClaw Vollstaendiges Ecosystem
Stand: 2026-02-08

---

## UEBERSICHT (Alle 6 Repos)

| Repo | Stars | Sprache | Zweck | Relevanz fuer Maurice |
|------|-------|---------|-------|----------------------|
| **openclaw/openclaw** | 175K | TypeScript | Personal AI Assistant - Gateway, Multi-Channel, Skills | KERN - Basis des ganzen Systems |
| **openclaw/clawhub** | 1.5K | TypeScript | Skill Registry / Marketplace | HOCH - Skills verkaufen |
| **openclaw/skills** | 718 | Python/JS | Backup-Archiv aller ClawHub Skills | MITTEL - Inspiration & Research |
| **openclaw/lobster** | 423 | TypeScript | Workflow Shell / Pipeline Engine | HOCH - Automation |
| **openclaw/nix-openclaw** | 282 | Nix | Deklarative Installation via Nix | NIEDRIG - Nur fuer Nix-User |
| **openclaw/openclaw-ansible** | 237 | Shell | Hardened Installation mit Security | MITTEL - Server-Deployment |

---

## OPENCLAW CORE (175K Stars)

### Was ist es?
OpenClaw (frueher Moltbot, davor Clawdbot) ist ein **selbst-gehosteter AI Assistant** der lokal laeuft.
- Gateway WebSocket auf `ws://127.0.0.1:18789`
- Unterstuetzt: WhatsApp, Telegram, Slack, Discord, Signal, Teams, Matrix, Google Chat
- Modelle: Anthropic Claude (Opus 4.6 empfohlen), OpenAI
- Node >= 22 erforderlich

### Installation
```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

### Key Features
- **Multi-Channel Inbox**: Verschiedene Channels zu isolierten Agent Workspaces routen
- **Voice**: Wake Word + Talk Mode (macOS/iOS/Android, ElevenLabs)
- **Live Canvas**: Visueller Agent-Workspace
- **Browser Control**: Chrome/Chromium Steuerung
- **Cron Jobs**: Zeitgesteuerte Automationen
- **Webhooks**: Event-getriebene Ausloeser
- **Skills Platform**: Bundled, Managed, Workspace-Level Skills
- **Sandbox Mode**: Docker-Container fuer Gruppen-Sessions

### Security
- DM Pairing Policy: Unbekannte Sender bekommen Pairing Codes
- Sandbox Mode: `agents.defaults.sandbox.mode: "non-main"`
- Remote Access: Tailscale Serve/Funnel oder SSH Tunnel

### Konfiguration
Minimal in `~/.openclaw/openclaw.json`:
```json
{
  "agent": {
    "model": "anthropic/claude-opus-4-6"
  }
}
```

### Workspace Struktur
- Root: `~/.openclaw/workspace`
- Prompts: `AGENTS.md`, `SOUL.md`, `TOOLS.md`
- Skills: `~/.openclaw/workspace/skills/<skill>/SKILL.md`

### Aktuelle Version
**openclaw 2026.2.2** - Web UI Agents Dashboard, Feishu/Lark Plugin, QMD Memory Backend

---

## LOBSTER (Workflow Shell) - 423 Stars

### Was ist es genau?
Lobster ist eine **typisierte Workflow-Shell** - ein lokaler "Macro Engine" der Skills und Tools zu **composable Pipelines** verbindet. Statt 10 einzelne LLM-Calls zu machen, buendelt Lobster alles in EINEN deterministischen Aufruf.

### Kernkonzept: Token-Effizienz
```
OHNE Lobster: 10 Tool-Calls x LLM-Overhead = teuer + langsam
MIT Lobster:  1 Tool-Call + strukturiertes Ergebnis = guenstig + schnell
```

### Key Features
- **Typed Pipelines**: JSON-Objekte statt Text-Streams
- **Approval Gates**: Harter Stopp vor Side-Effects (Email senden, Comment posten)
- **Resumable**: Workflow-Token speichern, spaeter fortsetzen
- **Persistent State**: "Letzter verarbeiteter Email-ID" bleibt erhalten
- **Deterministisch**: Pipelines sind Daten - leicht zu loggen, diffen, replyen

### Workflow-Format (.lobster)
```yaml
steps:
  - id: collect
    command: list --json
  - id: process
    stdin: $collect.stdout
    approval: required
  - id: execute
    condition: $approve.approved
```

### Tool API (JSON)
```json
{
  "action": "run",
  "pipeline": "command | pipe | approve",
  "timeoutMs": 30000,
  "maxStdoutBytes": 512000
}
```

Resume nach Approval:
```json
{
  "action": "resume",
  "token": "<resumeToken>",
  "approve": true
}
```

### Installation
```bash
# Im Repo:
pnpm install && pnpm test

# Aktivieren in OpenClaw Config:
{
  "tools": {"alsoAllow": ["lobster"]}
}
```

### Real-World Beispiel: Email Triage
```json
{
  "action": "run",
  "pipeline": "email.triage --limit 20",
  "timeoutMs": 30000
}
```
Returned Approval-Request -> User resumed mit `approve: true`.

### Composable Pipeline Beispiel
"Jeden Montag 9 Uhr: GitHub Issues mit Tag 'urgent' holen, Notion-Seite erstellen, an #dev-team Slack senden."

### Wie nutzt Maurice das?
1. **BMA-Workflows**: Inspektionschecklisten automatisieren
2. **Content-Pipeline**: SEO Research -> Artikel schreiben -> Publizieren - alles in einem Workflow
3. **Email-Automation**: Triage, Auto-Antwort, Follow-Up
4. **Sales-Pipeline**: Lead-Qualifizierung, CRM-Update, Angebot erstellen
5. **Token-Sparen**: Statt 10 Claude-Calls nur 1 Lobster-Aufruf

### LLM-Task Plugin
Ermoeglicht strukturierte LLM-Schritte innerhalb deterministic Pipelines:
```json
openclaw.invoke --tool llm-task --action json --args-json '{
  "prompt": "Klassifiziere Email-Intent",
  "input": {...},
  "schema": {"type":"object","properties":{...}}
}'
```

---

## CLAWHUB (Skill Marketplace) - 1.5K Stars

### Was ist es?
ClawHub ist die **oeffentliche Skill-Registry** fuer OpenClaw. Funktioniert wie "npm fuer AI Agents".
- URL: https://clawhub.ai/
- Komplett kostenlos (aktuell)
- Vector-basierte Suche (nicht nur Keywords)
- Semantic Versioning mit Changelogs

### Wie viele Skills?
- Knapp **4.000 Skills** im Registry (Stand Feb 2026)
- ~7.1% (283 Skills) mit Sicherheitsproblemen identifiziert (Snyk Audit)
- Kategorien: SEO, Content, DevOps, CRM, Social Media, Automation

### Skill-Format
Ein Skill = ein Ordner mit:
```
my-skill/
  SKILL.md          # Hauptdokumentation (Pflicht)
  config.json       # Konfiguration
  scripts/          # Unterstuetzende Scripts
```

### CLI Commands
```bash
# Installieren:
npm i -g clawhub   # oder: pnpm add -g clawhub

# Suchen:
clawhub search "calendar"

# Installieren:
clawhub install <skill-slug>

# Updaten:
clawhub update --all

# Publishen:
clawhub publish <path> --slug <slug> --version <version>

# Installierte auflisten:
clawhub list
```

### Wie publisht man eigene Skills?
1. GitHub Account (mindestens 1 Woche alt)
2. Skill-Ordner mit SKILL.md erstellen
3. `clawhub publish ./my-skill --slug my-awesome-skill --version 1.0.0`
4. Moderation-Review (automatisch nach 3+ Reports versteckt)
5. Community Feedback via Stars und Comments

### Revenue-Potential durch eigene Skills

**Aktuell ist ClawHub kostenlos** - kein direkter Verkauf auf der Plattform.

**ABER: Indirekte Monetarisierung ist moeglich:**
- Free-Tier + Premium Model (Basis gratis, Premium kostenpflichtig)
- Skills auf eigenem Marktplatz verkaufen ($10-200 je nach Komplexitaet)
- Skill-Bundles: Verwandte Skills als Pakete zu Rabatt
- Consulting: "Ich baue dir einen Custom Skill fuer deinen Use Case"

**Empfohlene Pricing-Strategie:**
- Kostenlose Basis-Version auf ClawHub (Downloads + Reviews sammeln)
- Premium-Version mit erweiterten Features kostenpflichtig anbieten

### SICHERHEITSWARNUNG (Stand Feb 2026)
- **341 malicious Skills** auf ClawHub identifiziert (HackerNews, Snyk)
- Atomic Stealer (AMOS) Malware ueber gefaelschte Skills verteilt
- 54% der schadhaften Skills zielen auf Crypto-Wallets
- **Empfehlung**: Immer SKILL.md und Scripts reviewen vor Installation
- Docker-Sandbox nutzen fuer unbekannte Skills
- Nur Skills von bekannten Maintainern installieren

---

## SKILLS ARCHIVE - 718 Stars

### Was ist drin?
- **Komplettes Backup aller ClawHub Skills** (alle Versionen)
- 15.816 Commits (sehr aktiv gepflegt)
- Sprachen: Python (46.5%), JavaScript (24.5%), Shell (11.7%), TypeScript (10.3%)
- MIT Lizenz

### Struktur
```
skills/
  <skill-slug>/
    <version>/
      SKILL.md
      ...
```

### Welche Skills sind fuer Maurice relevant?

**SEO & Content:**
- SEO Content Engine Skills (Keyword-Research, SERP-Analyse, Artikel-Generierung)
- Content Calendar Skills
- Schema.org Markup Generierung
- Meta Description Optimierung

**Business Automation:**
- Email Triage & Auto-Response
- CRM Integration
- Invoice Processing
- Task Management

**DevOps / Technical:**
- CI/CD Pipeline Skills
- Server Monitoring
- Log Analysis
- Incident Response

**Social Media:**
- Post-Scheduling
- Audience Analytics
- Content Distribution

### Nutzung als Inspiration
Das Archive ist perfekt um:
1. Bestehende Skill-Patterns zu studieren
2. SKILL.md Formate zu lernen
3. Populaere Skills zu identifizieren (nach Stars/Downloads)
4. Eigene Skills nach bewaehertem Muster zu bauen

---

## ANSIBLE (Hardened Installation) - 237 Stars

### Was macht es?
Automatisierte, gehaertete OpenClaw-Installation fuer Linux-Server:

### Security Stack
| Komponente | Funktion |
|-----------|----------|
| **Tailscale VPN** | Sicherer Remote-Zugriff ohne offene Ports |
| **UFW Firewall** | Nur SSH (22) + Tailscale (41641/udp) offen |
| **Fail2ban** | SSH Brute-Force Block nach 5 Fehlversuchen |
| **Docker Isolation** | Kein externer Port-Exposure |
| **Unattended Upgrades** | Automatische Security-Patches |
| **Non-Root User** | OpenClaw laeuft unprivilegiert |
| **systemd Hardening** | NoNewPrivileges, ProtectSystem |

### Installation
```bash
# Voraussetzungen: Debian 11+, Ubuntu 20.04+, oder macOS 11+
# Git + Ansible installiert

# Release Mode (Production):
# Installiert via pnpm install -g openclaw@latest

# Dev Mode:
# Klont Repo, baut aus Source, erstellt Aliases wie "openclaw-rebuild"
```

### Post-Installation
```bash
openclaw onboard --install-daemon
# Wizard konfiguriert WhatsApp/Telegram/Signal
```

### Sollte Maurice das nutzen?
**JA, wenn:**
- Maurice einen Server (VPS/Cloud) fuer OpenClaw nutzen will
- Remote-Zugriff auf OpenClaw noetig ist
- Mehrere Clients gleichzeitig zugreifen sollen
- Production-Grade Security gewuenscht ist

**NEIN, wenn:**
- OpenClaw nur lokal auf dem MacBook laeuft
- Kein Server vorhanden ist

---

## NIX (Package Manager) - 282 Stars

### Was macht es?
Deklarative OpenClaw-Installation via Nix/Home Manager.

### Key Features
- **Deterministische Builds**: Exakte Versions-Pinning
- **Instant Rollback**: `home-manager switch --rollback`
- **Plugin-Isolation**: Jedes Plugin deklariert eigene CLI-Tools
- **LaunchD/SystemD Integration**: Automatischer Service-Start

### Bundled Plugins
| Plugin | Funktion |
|--------|----------|
| summarize | URLs, PDFs, YouTube zusammenfassen |
| peekaboo | Screenshots |
| oracle | Web-Suche |
| poltergeist | macOS UI Automation |
| sag | Text-to-Speech |
| camsnap | Kamera-Snapshots |
| gogcli | Google Calendar |
| goplaces | Google Places API |
| bird | Twitter/X Integration |
| sonoscli | Sonos-Steuerung |
| imsg | iMessage |

### Relevant fuer Maurice?
**NIEDRIG** - Nix hat eine steile Lernkurve. Die Standard-Installation via npm ist einfacher.
**ABER**: Wenn Maurice reproduzierbare Deployments auf mehreren Maschinen will, ist Nix unschlagbar.

---

## INTEGRATION PLAN: Alle 6 Repos optimal nutzen

### Phase 1: Basis (Sofort)
1. **OpenClaw installieren** via `npm install -g openclaw@latest`
2. **Skills erkunden** auf https://clawhub.ai/ - NUR verifizierte Skills installieren
3. **Lobster aktivieren** in der OpenClaw Config:
   ```json
   {"tools": {"alsoAllow": ["lobster"]}}
   ```

### Phase 2: Automation (Woche 1-2)
4. **Lobster Workflows erstellen** fuer wiederkehrende Tasks:
   - SEO Content Pipeline
   - Email Triage
   - Social Media Posting
   - BMA Inspektionschecklisten
5. **Skills Archive klonen** fuer Inspiration:
   ```bash
   git clone https://github.com/openclaw/skills.git --depth 1
   ```

### Phase 3: Monetarisierung (Woche 2-4)
6. **Eigene Skills auf ClawHub publishen**:
   - BMA-spezifische Skills (Nischenmarkt, wenig Konkurrenz)
   - SEO Content Skills (hohe Nachfrage)
   - Business Automation Skills
7. **Lobster Workflows als Service anbieten**

### Phase 4: Production (Monat 2)
8. **Ansible Setup** fuer Server-Deployment (wenn Remote-Zugriff noetig)
9. **Nix** nur evaluieren wenn Multi-Machine Deployment geplant

---

## MONETARISIERUNG

### 1. Eigene Skills auf ClawHub verkaufen
| Skill-Typ | Preis | Potential |
|-----------|-------|-----------|
| BMA Inspektions-Skill | $50-100 | Nische, wenig Konkurrenz |
| SEO Content Engine | $100-200 | Hohe Nachfrage |
| Email Automation | $30-50 | Massenmarkt |
| Business Automation Bundle | $200+ | Premium-Segment |

**Strategie**: Free-Tier auf ClawHub (Downloads sammeln) + Premium auf eigener Seite

### 2. SEO Content als Service (mit OpenClaw Skills)
- SEO-Artikel automatisiert mit OpenClaw produzieren
- Verkauf auf Fiverr/Upwork: $100-300 pro Artikel
- Bei 2-5 Artikeln/Tag = **$6.000-$45.000/Monat**
- OpenClaw + Lobster = fast vollautomatische Pipeline

### 3. Lobster Workflows als Service
- Custom Workflow-Erstellung fuer Unternehmen
- Consulting: $100-200/Stunde
- "Ich automatisiere deinen Business-Prozess mit OpenClaw"
- Wiederkehrende Revenue durch Maintenance-Vertraege

### 4. Ansible Setup als Consulting Service
- Gehaertete OpenClaw-Installation fuer Firmen
- Tailscale VPN + Security Hardening = Premium-Service
- $500-2.000 pro Setup
- Zielgruppe: KMU die AI-Assistenten sicher deployen wollen

### 5. Skill-Bundles & Pakete
- Verwandte Skills buendeln (z.B. "Complete SEO Suite")
- Rabattierte Pakete erhoehen Conversion
- Cross-Selling zwischen eigenen Skills

### 6. Affiliate / Empfehlungen
- OpenClaw-Setup-Guides mit Affiliate-Links
- Hosting-Empfehlungen (VPS fuer OpenClaw)
- Tool-Empfehlungen die mit Skills integrieren

---

## RISIKEN & WARNUNGEN

### Security (KRITISCH - Stand Feb 2026)
- **341+ schaedliche Skills** auf ClawHub identifiziert
- Atomic Stealer Malware verbreitet sich ueber gefaelschte Skills
- 7.1% aller Skills haben Sicherheitslecks (API-Key Exposure)
- **NIEMALS** unbekannte Skills ohne Review installieren
- **IMMER** Docker-Sandbox fuer Tests nutzen
- Skills die "Prerequisites" installieren wollen besonders pruefen

### Empfohlene Sicherheitsmassnahmen
1. Nur Skills von verifizierten Publishern installieren
2. SKILL.md und Scripts VOR Installation lesen
3. Sandbox Mode aktivieren: `agents.defaults.sandbox.mode: "non-main"`
4. Eigene Skills auditieren lassen vor Publikation
5. Keine API-Keys in Skills hardcoden
6. Regelmaessig `clawhub update --all` ausfuehren

---

## QUICK REFERENCE

### Wichtigste URLs
- OpenClaw Docs: https://docs.openclaw.ai/
- ClawHub: https://clawhub.ai/
- Lobster Docs: https://docs.openclaw.ai/tools/lobster
- ClawHub Docs: https://docs.openclaw.ai/tools/clawhub
- Skills Docs: https://docs.openclaw.ai/tools/skills

### Wichtigste Commands
```bash
# OpenClaw installieren
npm install -g openclaw@latest
openclaw onboard --install-daemon

# ClawHub CLI
npm i -g clawhub
clawhub search "seo"
clawhub install <slug>
clawhub publish ./my-skill --slug my-skill --version 1.0.0

# Lobster
node ./bin/lobster.js doctor
lobster run path/to/workflow.lobster

# Status
openclaw status
/status  (im Chat)
```

### Config-Dateien
```
~/.openclaw/openclaw.json     # Haupt-Config
~/.openclaw/workspace/        # Workspace Root
~/.openclaw/workspace/skills/ # Installierte Skills
```

---

## FAZIT

OpenClaw ist mit 175K Stars das groesste Open-Source AI Agent Projekt. Das Ecosystem bietet:

1. **Lobster** = Workflow Engine die Token spart und Automationen deterministisch macht
2. **ClawHub** = Marketplace mit ~4000 Skills, Revenue-Potential durch eigene Skills
3. **Skills Archive** = Goldgrube fuer Inspiration und Pattern-Learning
4. **Ansible** = Production-Grade Security fuer Server-Deployments
5. **Nix** = Deklarative Deployments fuer Fortgeschrittene

**Maurices groesste Chance**: SEO Content Skills + Lobster Workflows = automatisierte Content-Produktion als Service. Potential: $6.000-$45.000/Monat bei geringem Aufwand nach initialem Setup.

**Naechster Schritt**: OpenClaw installieren, Lobster aktivieren, ersten SEO-Workflow bauen.
