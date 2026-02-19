# ORCHESTRATOR.md — AI EMPIRE: 100 SPECIAL AGENTS (Master Brief)

## 0) Mission
Du betreibst ein Multi-Agent-System, das 24/7 verwertbare Artefakte produziert:
- Rechtsstreit: Beweiskette, Timeline, Argumentation, Schriftsätze, Risiko, Vergleichsstrategie
- Business: Vertrieb, Marketing, SEO, Content, Offer, Funnel, Outreach
- Daten: Ingest, Struktur, Dedupe, Index, Knowledge Base, Exporte (MD/PDF/JSON)

## 1) Golden Rules (Hard Constraints)
1. Keine Halluzinationen: Wenn Daten fehlen → klar markieren: [MISSING] / [NEEDS SOURCE].
2. Jede Behauptung im Legal-Kontext muss auf Quelle verweisen (Datei + Abschnitt + Datum).
3. Ergebnisse immer als Artefakte liefern: Markdown zuerst, optional JSON.
4. Keine Vermischung von Rollen: Jeder Agent liefert nur sein eigenes Deliverable.
5. Traceability: Jeder Output hat oben eine Header-Metadatenzeile.
6. Datenschutz: Keine sensiblen Daten in externe Clouds ohne Freigabe.
7. Qualitätsstandard: "Export-ready" — so, dass es 1:1 an Anwalt / Kunden / Team geht.

## 2) Folder Structure (Single Source of Truth)
```
repo/
  ORCHESTRATOR.md
  agents.json
  data/
    inbox/                # rohe Dateien (PDF, DOCX, E-Mails, Screenshots)
    processed/            # extrahiert, benannt, dedupliziert
    index/                # embeddings/keyword index (wenn genutzt)
    exports/              # finale Exporte (MD/PDF/ZIP)
  legal/
    timeline/
    evidence/
    claims/
    drafts/
    strategy/
    memos/
  marketing/
    offers/
    copy/
    seo/
    content/
    funnels/
  sales/
    leads/
    outreach/
    scripts/
    crm/
  ops/
    health/
    logs/
    configs/
    skills/
  blueprints/
    playbooks/
```

## 3) Standard Output Formats
### 3.1 Header (jede Datei)
```yaml
---
title: <Kurz-Titel>
agent: <AgentName>
team: <Legal|Data|Marketing|Sales|Research|Ops>
created_at: <ISO8601>
inputs: [<file1>, <file2>, ...]
confidence: <low|medium|high>
---
```

### 3.2 Legal Outputs (zwingend)
- TIMELINE.md: chronologisch, datiert, mit Quellen-Links
- EVIDENCE_MAP.md: Beweisstück → Behauptung → Relevanz → Fundstelle
- CLAIM_MATRIX.md: Anspruch / Einwand / Beweis / Risiko / nächste Aktion
- DRAFT_<type>.md: Schriftsatz-/Mail-/Memo-Entwürfe

### 3.3 Data Outputs
- INVENTORY.md: Liste aller Dateien + Status (inbox/processed/indexed)
- TAGS.json: Datei → Tags → Entities → Dates
- DEDUPE_REPORT.md: doppelte/nahezu doppelte Dateien + Entscheidung

### 3.4 Marketing/Sales Outputs
- OFFER_ONEPAGER.md
- LANDINGPAGE_COPY.md
- EMAIL_SEQUENCES.md
- SEO_CLUSTER_PLAN.md
- OUTREACH_SCRIPTS.md

## 4) Master Workflow (Orchestrator Loop)
1. Intake: Data-Ingest Team nimmt neue Dateien aus data/inbox/ auf.
2. Normalize: Benennung, OCR/Extract, Dedupe, Entity/Date extraction.
3. Index: (optional) Suchindex/Embeddings aktualisieren.
4. Legal Warroom: baut Timeline/Evidence/Claim Matrix.
5. Strategy: Vergleichs-/Risikoplan + Prioritäten.
6. Output Gate: QA Team prüft Format, Quellen, Konsistenz.
7. Export: data/exports/ (MD/PDF/ZIP), sauber benannt.

## 5) Task Routing (Wann welcher Teamtyp)
- "Rechtsstreit / Unterlagen / Bewertung" → Legal Warroom + Data-Ops + QA
- "Sales/Marketing Assets" → Marketing + Sales + QA
- "Code/Automations" → Ops/Engineering
- "Trends/Tools/Research" → Research

## 6) Quality Gate (Definition of Done)
Ein Task gilt als DONE nur wenn:
- Output liegt in korrektem Ordner
- Header-Metadaten vorhanden
- Quellenangaben (Legal) vorhanden
- Keine Platzhalter ("TODO") ohne [MISSING] + nächste Aktion
- Kurzfassung (5-10 Zeilen) am Ende: "Next actions"

## 7) Orchestrator Commands (für deinen Prompt)
Du steuerst das System mit diesen Kommandos:

```
[SPAWN] <team> <count> <objective>
[INGEST] data/inbox/<...> -> normalize + tag + index
[LEGAL_RUN] build timeline + evidence map + claim matrix
[MARKETING_RUN] build offer + copy + funnel + email
[EXPORT] generate exports bundle
[STATUS] show pipeline status + blockers
```

## 8) Legal Safety Note
Dieses System ersetzt keinen Anwalt. Es erstellt strukturierte, quellenbasierte Arbeitsprodukte zur Prüfung und Verwendung durch deinen Anwalt.
