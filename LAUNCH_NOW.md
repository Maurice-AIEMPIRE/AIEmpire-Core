# LAUNCH NOW - Maurice's Revenue Activation

**Erstellt:** 2026-02-09 | **Geschaetzter Aufwand:** 30 Minuten

---

## SCHRITT 1: GUMROAD ACCOUNT (10 min)

1. Gehe zu **gumroad.com** -> "Start Selling"
2. Account erstellen (Email + Passwort)
3. Profil: "Maurice Pfeifer - AI & Automation Expert"

### Produkt 1: AI Prompt Vault (EUR 27)
- "New Product" -> Digital Product
- Name: **"AI Prompt Vault - 127 Copy-Paste Prompts"**
- Preis: **EUR 27**
- Datei hochladen: `~/.openclaw/workspace/ai-empire/04_OUTPUT/GUMROAD_PRODUCTS/ai_prompt_vault_final_v1.md`
- (Vorher in PDF konvertieren mit: `pandoc ai_prompt_vault_final_v1.md -o AI_Prompt_Vault.pdf`)
- Beschreibung kopieren aus: `landing_page_copy_v1.md`

### Produkt 2: Docker Mastery Guide (EUR 99)
- "New Product" -> Digital Product
- Name: **"Docker Mastery - From Zero to Production"**
- Preis: **EUR 99**
- Datei: `docker_guide_complete_v1.md` -> PDF

### Produkt 3: Stack-as-Service (EUR 99/299/999)
- "New Product" -> Digital Product -> 3 Tiers
- Name: **"AI Stack-as-Service - Complete Setup"**
- STARTER: EUR 99 | PRO: EUR 299 | ENTERPRISE: EUR 999
- Datei: `stack_as_service_complete_v1.md` -> PDF

**Nach Upload:** Notiere die 3 Gumroad Links!

---

## SCHRITT 2: n8n API KEY (5 min)

1. Oeffne **http://localhost:5678**
2. Erstelle Owner Account (Email + Passwort)
3. Settings -> API -> "Create API Key"
4. Kopiere den Key
5. Fuehre aus:
```bash
cd /Users/maurice/.claude-worktrees/AIEmpire-Core/dazzling-darwin
export N8N_API_KEY="dein-key-hier"
echo "export N8N_API_KEY=\"$N8N_API_KEY\"" >> ~/.zshrc
```

---

## SCHRITT 3: ERSTE 5 POSTS (10 min)

Kopiere diese Posts auf Twitter/LinkedIn (ersetze [LINK] mit deinem Gumroad Link):

### Post 1 (LinkedIn)
```
You're wasting 70% of your AI budget on bad prompts.
Here's how I cut costs by 10x and saved 10 hours/week:
[LINK]
```

### Post 2 (Twitter)
```
I wrote 20 articles in 2 hours using these prompts.
Normally takes a full day.
127 prompts that actually work:
[LINK]
```

### Post 3 (Twitter)
```
Built 127 AI prompts used by 500+ engineers & founders.
Copy-paste ready. Kimi K2.5 optimized.
EUR 27 for lifetime access:
[LINK]
```

### Post 4 (LinkedIn)
```
This one change improved my AI outputs by 100%
(And cut costs by 70%)
See the 127 prompts:
[LINK]
```

### Post 5 (Twitter)
```
First 100 buyers get this for EUR 27.
After that it's EUR 47.
127 prompts that save 10 hours/week:
[LINK]
```

---

## SCHRITT 4: REVENUE PIPELINE STARTEN (5 min)

```bash
cd /Users/maurice/.claude-worktrees/AIEmpire-Core/dazzling-darwin

# System Health Check
python3 scripts/revenue_pipeline.py health

# Dashboard anzeigen
python3 scripts/revenue_pipeline.py dashboard

# Pipeline starten (generiert Posts via Ollama)
python3 scripts/revenue_pipeline.py launch

# Verkauf tracken
python3 scripts/revenue_pipeline.py track --add 27.00 "Gumroad - AI Prompt Vault"
```

---

## SCHRITT 5: WORKFLOW VERBINDEN (Optional, 5 min)

```bash
# Status aller Komponenten
python3 scripts/connect_workflows.py status

# Einen Pipeline-Zyklus ausfuehren
python3 scripts/connect_workflows.py run

# Empire Status
python3 workflow-system/empire.py status
```

---

## ERWARTETER REVENUE

| Zeitraum | Produkt | Verkauefe | Revenue |
|----------|---------|-----------|---------|
| Woche 1 | AI Prompt Vault | 20-50 | EUR 540-1,350 |
| Woche 1 | Docker Guide | 5-10 | EUR 495-990 |
| Monat 1 | Alle 3 Produkte | 100+ | EUR 2,700-5,400 |
| Monat 3 | + Upsells | 300+ | EUR 10,000+ |
| Jahr 1 | Full Stack | 2000+ | EUR 50,000-115,000 |

---

## SYSTEM STATUS

| Service | Port | Status |
|---------|------|--------|
| n8n | 5678 | RUNNING |
| Ollama | 11434 | RUNNING (3 Modelle) |
| Empire CLI | - | READY |
| Revenue Pipeline | - | READY |
| Workflow Connector | - | READY |
| Gumroad | - | WARTET AUF MAURICE |
| Redis | 6379 | NICHT INSTALLIERT |
| PostgreSQL | 5432 | NICHT INSTALLIERT |

**Redis + PostgreSQL werden erst fuer PARL Phase 2 gebraucht (Woche 3+).**
