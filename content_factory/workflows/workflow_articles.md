# Workflow: Long-Form X Articles

## OVERVIEW
Produktion von X long-form Articles (800-2500 Woerter) fuer Thought Leadership, Storytelling, Technical Deep Dives.

## PIPELINE (5 Schritte)

### SCHRITT 1: Konzept und Thema
Agent: Ideation Agent (existing)
Input: NISCHE, ZIELGRUPPE, Anzahl Artikel-Ideen
Aufgabe: Generiere Artikel-Konzepte mit Arbeitstitel, Angle, Key Value Proposition
Output: Liste von Artikel-Konzepten
Zeit: 5-10 Minuten pro 10 Konzepte

### SCHRITT 2: Outline Erstellung
Agent: Article Outliner (NEW - prompts/article_outliner.md)
Input: Artikel-Konzept, ARTIKELTYP, NISCHE, STIL
Aufgabe: Detaillierte Struktur (6-10 Sektionen), Flow definieren, Key Points pro Sektion
Output: Artikel Outline mit Flow-Check
Zeit: 10-15 Minuten pro Outline

Qualitaetskriterien:
- Hook in Sektion 1 stark genug
- Logischer Flow zwischen Sektionen
- Value klar erkennbar in jeder Sektion
- CTA natuerlich integriert

### SCHRITT 3: Artikel Writing
Agent: Article Writer (NEW - prompts/writer_articles.md)
Input: Outline, NISCHE, STIL, SPRACHE, TON
Aufgabe: Vollstaendigen Artikel schreiben (800-2500 Woerter)
Output: Raw Article (erster Draft)
Zeit: 20-30 Minuten pro Artikel

Qualitaetskriterien:
- Wortanzahl im Target Range
- Hook fesselt in ersten 100 Woertern
- Jede Sektion hat klaren Value
- Authentischer Ton (kein Corporate-Speak)

### SCHRITT 4: Refinement
Agent: Article Refiner (NEW - prompts/article_refiner.md)
Input: Raw Article, Original Outline
Aufgabe: Flow, Klarheit, Engagement, Pacing verbessern
Output: Refined Article (final draft)
Zeit: 15-20 Minuten pro Artikel

Qualitaetskriterien:
- Flow Score 8/10+
- Klarheits-Score 9/10+
- Engagement-Score 8/10+
- Value Density 8/10+

### SCHRITT 5: Final Check
Agent: Orchestrator (existing)
Input: Refined Article, Original Konzept
Aufgabe: Vision-Check, Zielgruppen-Fit, Brand-Alignment, Technical Check
Output: Finaler Artikel + Quality Report
Zeit: 5-10 Minuten

## BATCH PROCESSING (10 Artikel)

1. Ideation fuer alle 10 Konzepte (30 Min)
2. Outlines fuer alle 10 Artikel (2 Std)
3. Writing in 2er-Gruppen (5x Writing Sessions a 1 Std)
4. Refinement in 2er-Gruppen (5x Refining Sessions a 45 Min)
5. Final Check fuer alle 10 (1 Std)

Gesamtzeit fuer 10 Artikel: 10-12 Stunden
Pro Artikel: 1-1.5 Stunden

## PARALLELISIERUNG

- Ideation + Outlining koennen parallel fuer mehrere Themen laufen
- Writing kann parallel mit 2-3 Writer Agents (unterschiedliche Artikel)
- Refinement kann parallel sobald Raw Articles fertig sind

## OUTPUT LOCATION

deliverables/articles/ARTICLE_[NN]_[TITEL_SLUG].md

## ARTIKELTYPEN

- Hero Journey: Nutze prompts/hero_journey_template.md als Basis
- How-To: Step-by-Step Guide mit Commands/Screenshots
- Case Study: Vorher/Nachher mit konkreten Metriken
- Technical Deep Dive: Architecture + Implementation Details
