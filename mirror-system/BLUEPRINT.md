# DOPPELHELIX BLUEPRINT: Main Brain (Mac) + Mirror Lab (Gemini)

**Version:** 1.0
**Created:** 2026-02-10
**Owner:** Maurice Pfeifer

---

## ARCHITEKTUR-ÜBERSICHT

```
┌─────────────────────────────────────┐     ┌──────────────────────────────────────┐
│         MAIN BRAIN (Mac)            │     │         MIRROR LAB (Gemini)          │
│         ================            │     │         ==================           │
│                                     │     │                                      │
│  ┌─────────┐  ┌──────────────┐     │     │  ┌───────────┐  ┌──────────────┐    │
│  │ OpenClaw │  │ Workflow     │     │     │  │ Vertex AI │  │ Agent Farm   │    │
│  │ Agents   │  │ System       │     │     │  │ (Gemini)  │  │ (Cloud Run)  │    │
│  └────┬─────┘  └──────┬───────┘     │     │  └─────┬─────┘  └──────┬───────┘    │
│       │               │             │     │        │               │            │
│  ┌────┴───────────────┴──────┐     │     │  ┌─────┴───────────────┴──────┐     │
│  │     Empire Control        │     │     │  │     Mirror Orchestrator    │     │
│  │     Center (empire.py)    │     │     │  │     (mirror_brain.py)      │     │
│  └────────────┬──────────────┘     │     │  └────────────┬──────────────┘     │
│               │                     │     │               │                    │
│  ┌────────────┴──────────────┐     │     │  ┌────────────┴──────────────┐     │
│  │   Export Paket Generator  │─────┼──git──│   Import + Analyse Engine  │     │
│  │   (export_daily.py)       │     │push  │  (analyze_export.py)        │     │
│  └───────────────────────────┘     │     │  └────────────┬──────────────┘     │
│               ▲                     │     │               │                    │
│               │                     │     │  ┌────────────┴──────────────┐     │
│  ┌────────────┴──────────────┐     │     │  │   PR Factory              │     │
│  │   Merge Gate              │◄────┼──PR──│   (pr_factory.py)           │     │
│  │   (merge_gate.py)         │     │     │  └───────────────────────────┘     │
│  └───────────────────────────┘     │     │                                    │
│                                     │     │  ┌───────────────────────────┐     │
│  ┌───────────────────────────┐     │     │  │   Mirror Memory (GCS)     │     │
│  │  DIP Engine               │◄───┼──sync─│  gs://ai-empire-mirror/     │     │
│  │  (daily_interrogation.py) │     │     │  └───────────────────────────┘     │
│  └───────────────────────────┘     │     │                                    │
│                                     │     │  ┌───────────────────────────┐     │
│  ┌───────────────────────────┐     │     │  │   Product Factory         │     │
│  │  Product Factory (local)  │◄───┼──PRs──│  (product_engine.py)       │     │
│  │  (product_pipeline.py)    │     │     │  └───────────────────────────┘     │
│  └───────────────────────────┘     │     │                                    │
└─────────────────────────────────────┘     └──────────────────────────────────────┘

                    ▲                                        │
                    │         GIT (Nervenstrang)              │
                    └────────────────────────────────────────┘
                              Pull-basiert
                         Cloud schlägt vor
                         Mac entscheidet
```

---

## 1. ROLLEN & GRENZEN

### Main Brain (Mac, Offline)
- **Rolle:** Single Source of Truth für Produktion
- **Aufgaben:** Legal-Warroom, Content, Ops, Indexing, Automationen
- **Output:** Telemetrie (JSONL), Artefakte, Gold Nuggets
- **Modelle:** Ollama (95%), Kimi (4%), Claude (1%)
- **Rechte:** ALLES - volle Kontrolle

### Mirror Lab (Gemini, Cloud)
- **Rolle:** R&D, Experimente, Skalierung
- **Aufgaben:** Neue Agenten, Prompt-Optimierung, Code-Reviews, Feature-PRs
- **Output:** Pull Requests, Reports, Benchmarks, Patches
- **Modelle:** Gemini 2.5 Pro/Flash
- **Rechte:** NUR lesen + PRs erstellen. Kein direkter Schreibzugriff auf Mac.

### GOLDENE REGEL: Cloud darf vorschlagen, Mac entscheidet.

---

## 2. DATENFLUSS

### Mac → Cloud (Export, sanitized)
```
1. export_daily.py sammelt:
   - system_status.json (Services, Uptime, Fehler)
   - task_log.jsonl (was wurde gemacht, Dauer, Ergebnis)
   - index_summary.json (Dateistruktur, Änderungen)
   - open_tasks.json (offene Aufgaben)
   - error_patterns.json (wiederkehrende Fehler)
   - vision_state.json (aktuelle Vision + Prioritäten)

2. REDACTION: Folgendes wird ENTFERNT:
   - API Keys, Tokens, Secrets
   - Private Vault Inhalte (Legal, Finanzen, Persönlich)
   - Vollständige Dokumente (nur Summaries)

3. Push als Git Tag: export/YYYY-MM-DD
   ODER: Upload zu GCS: gs://ai-empire-mirror/exports/
```

### Cloud → Mac (PRs, kontrolliert)
```
1. Cloud analysiert Export-Paket
2. Cloud erstellt Verbesserungen auf Branches:
   - mirror/fix-* (Bugfixes)
   - mirror/feat-* (Features)
   - mirror/opt-* (Optimierungen)
   - mirror/agent-* (neue Agenten)
3. Jeder Branch hat:
   - CHANGELOG.md (was + warum)
   - tests/ (automatische Tests)
   - benchmark.json (vorher/nachher Metriken)
4. Mac: merge_gate.py prüft:
   - [ ] Tests grün?
   - [ ] Keine Secrets im Code?
   - [ ] Keine Cloud-API-Calls ohne CLOUD_MODE?
   - [ ] Diff < 500 Zeilen?
   - [ ] CHANGELOG vorhanden?
   → Merge nur wenn ALLES grün
```

---

## 3. DAILY INTERROGATION PROTOCOL (DIP)

### Morgens (10 Min, 10 Fragen)

**Block A – Vision (Wohin?)**
1. Was ist heute der EINE Output, der dich real weiterbringt?
2. Welche 3 Dinge wären heute ein "Sieg"?
3. Was darf heute NICHT passieren?

**Block B – Prioritäten (Was?)**
4. Welche 2 Projekte sind die "Hauptfronten"?
5. Was ist aktuell die größte Blockade?
6. Wenn du nur 60 Minuten hättest: worauf?

**Block C – Regeln & Stil (Wie?)**
7. Mehr Risiko oder mehr Stabilität – heute?
8. Welche Kommunikation willst du (hart/knapp/freundlich/ausführlich)?
9. Was soll das System ignorieren (Noise)?

**Block D – Kontext (Was ist neu?)**
10. Neue Infos (Anwalt, Kunden, Finanzen, Gesundheit)?

### Abends (5 Min, 3 Fragen)
11. Was hat dich heute am meisten Zeit gekostet?
12. Welche Entscheidung war falsch/zu langsam?
13. Welche Aufgabe soll morgen automatisch vorbereitet sein?

### Output
- `vision_state.json` → Beide Systeme lesen das
- `task_orders.md` → Priorisierte Aufgaben für den Tag
- `decisions_log.jsonl` → Append-only Entscheidungshistorie

---

## 4. PRODUCT FACTORY PIPELINE

### Schritt 1: Idea Inbox
```
data/ideas/inbox.jsonl
Format: {"id": "...", "title": "...", "source": "...", "tags": [...], "ts": "..."}
```

### Schritt 2: Idea Scoring (automatisch)
```
Score-Dimensionen (1-10):
- payment_willingness: Würde jemand dafür zahlen?
- speed_to_market: Wie schnell lieferbar?
- reusability: Wie oft verkaufbar?
- compliance: Rechtlich sauber?
- signature_factor: Wie einzigartig für Maurice?

Output: runs/products/idea_ranked.csv
```

### Schritt 3: Offer Design
```
Für jede Top-Idee:
- target_audience: 1 Satz
- promise: Was bekommt der Käufer?
- modules: Inhaltsstruktur
- deliverables: Konkrete Dateien
- pricing: 3-Tier (Basic/Pro/Elite)

Output: runs/products/<product_id>/offer.md
```

### Schritt 4: Asset Production
```
Agenten bauen:
- PDF/Docs (Ollama → Markdown → PDF)
- Templates (Excel, Notion, PDF)
- Beispiel-Dateien
- Quickstart Guide

Output: products/<product_id>/bundle/*
```

### Schritt 5: Marketing Engine
```
Pro Produkt:
- 30 Social Posts (X/LinkedIn)
- 5 Threads (Deep Dive)
- 3 Hooks (Attention Grabber)
- Landing Copy
- Email Sequence (5 Emails)

Output: marketing/<product_id>/*
```

### Schritt 6: Distribution
```
- Gumroad / LemonSqueezy Upload
- Checkout-Link generieren
- Automatische Auslieferung

Output: sales/<product_id>/delivery.md
```

### Schritt 7: Feedback Loop
```
- Käuferfragen → FAQ → Produkt verbessern
- CTR/Conversion → Messaging optimieren
- Bewertungen → Testimonials extrahieren

Output: runs/metrics.json
```

---

## 5. CLOSED-LOOP OPTIMIERUNG

### Performance Loop (täglich)
```
Mac meldet:
  → Was funktioniert? (success_log.jsonl)
  → Wo langsam? (latency_log.jsonl)
  → Wo Fehler? (error_log.jsonl)
  → Was verschoben? (deferred_tasks.json)

Cloud antwortet:
  → Patch-PRs
  → Neue Agenten-Profile
  → Prompt-Optimierungen
  → Benchmarks (vorher/nachher)
```

### Vision Loop (täglich)
```
DIP Fragen → Maurice antwortet
  → vision_state.json aktualisiert
  → Router-Gewichte angepasst
  → Teamgröße skaliert
  → Fokus verschoben
```

---

## 6. SICHERHEIT & PRIVACY

### TABU für Cloud (niemals hochladen):
- Private Vault (Legal, Finanzen, Persönlich)
- API Keys, Tokens, Secrets
- Mandatsunterlagen, Verträge
- Gesundheitsdaten
- Private Fotos/Videos
- Vollständige Kundendaten

### Privacy Levels:
- **P0 (Public):** Code, Marketing, Produkt-Beschreibungen → Cloud OK
- **P1 (Internal):** Logs, Metriken, Task-Listen → Cloud OK (redacted)
- **P2 (Confidential):** Strategien, Finanzzahlen → Cloud nur Summaries
- **P3 (Restricted):** Legal, Private Vault → NIEMALS Cloud

### Merge Gate Checks:
- Keine Secrets im Code
- Keine Cloud-API-Calls ohne CLOUD_MODE Flag
- Keine Löschungen ohne explizite Genehmigung
- Diff < 500 Zeilen pro PR
- Tests müssen grün sein

---

## 7. VERZEICHNISSTRUKTUR

```
mirror-system/
├── BLUEPRINT.md              # Dieses Dokument
├── config/
│   ├── mirror_config.json    # Cloud-Verbindung, Buckets, Limits
│   ├── privacy_rules.json    # Was darf/darf nicht in die Cloud
│   ├── merge_rules.json      # Merge Gate Regeln
│   └── product_scoring.json  # Scoring-Gewichte für Product Factory
├── export/
│   ├── export_daily.py       # Tägliches Export-Paket erstellen
│   ├── redactor.py           # Secrets/Private Daten entfernen
│   └── exports/              # Archiv der Export-Pakete
├── import/
│   ├── merge_gate.py         # Prüfe + merge Cloud-PRs
│   └── imports/              # Empfangene Cloud-Reports
├── dip/
│   ├── daily_interrogation.py  # Fragen-Motor
│   ├── vision_state.json       # Aktueller Vision-Stand
│   ├── task_orders.md          # Tagesaufgaben
│   ├── decisions_log.jsonl     # Entscheidungshistorie
│   └── templates/              # Frage-Templates
├── product-factory/
│   ├── product_pipeline.py     # Gesamte Pipeline
│   ├── idea_scorer.py          # Ideen bewerten
│   ├── offer_designer.py       # Angebot erstellen
│   ├── asset_builder.py        # Assets produzieren
│   ├── marketing_engine.py     # Marketing Content
│   ├── data/
│   │   └── ideas/
│   │       └── inbox.jsonl     # Ideen-Eingang
│   ├── runs/
│   │   └── products/           # Aktive Produkt-Runs
│   └── products/               # Fertige Produkte
├── sync/
│   ├── sync_manager.py         # Koordiniert alle Sync-Ops
│   ├── telemetry_collector.py  # Sammelt Metriken
│   └── logs/                   # Sync-Logs
└── cloud/
    ├── mirror_brain.py         # Cloud-Orchestrator (läuft auf Gemini)
    ├── analyze_export.py       # Export-Analyse
    ├── pr_factory.py           # PR-Generator
    └── product_engine.py       # Cloud Product Factory
```

---

## 8. SETUP ROADMAP

### Phase 1: HEUTE (Minimal Mirror)
- [x] Blueprint erstellen
- [ ] Verzeichnisstruktur anlegen
- [ ] export_daily.py bauen
- [ ] DIP Engine (daily_interrogation.py) bauen
- [ ] vision_state.json initialisieren
- [ ] Product Factory Pipeline Grundstruktur

### Phase 2: DIESE WOCHE (PR-Fabrik)
- [ ] merge_gate.py implementieren
- [ ] Cloud mirror_brain.py Template
- [ ] Erste automatische PRs testen
- [ ] Product Scoring aktiv

### Phase 3: NÄCHSTE WOCHE (Vision Loop)
- [ ] DIP läuft täglich automatisch
- [ ] vision_state.json steuert Router-Gewichte
- [ ] Erste Produkte durch Pipeline

### Phase 4: MONAT 1 (Verdopplung messbar)
- [ ] Metriken: Durchsatz, Fehlerquote, Revenue
- [ ] Weekly Review → Cloud optimiert Systeme
- [ ] Product Factory liefert 2+ Produkte/Woche
