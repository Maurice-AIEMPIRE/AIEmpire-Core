# GOLD NUGGET: Dexter -- OpenClaw + Claude Code fuer Finance
Stand: 2026-02-08

---

## WAS IST ES?

**Dexter** ist ein autonomer AI-Agent fuer tiefe Finanzrecherche, erstellt von **Virat Singh** (GitHub: virattt).

- **Tagline:** "Claude Code, but for finance"
- **GitHub:** https://github.com/virattt/dexter
- **Stars:** 11.600+ | **Forks:** 1.400+ | **Contributors:** 10
- **Lizenz:** MIT (komplett frei nutzbar, auch kommerziell!)
- **Latest Release:** v2026.2.6 (6. Februar 2026)
- **Commits:** 285
- **Sprache:** TypeScript (98.7%), laeuft auf Bun Runtime

### Wer ist Virat Singh?
- Gruender von **financialdatasets.ai** (die Daten-API hinter Dexter)
- Betreibt auch **ai-hedge-fund** (45.600+ Stars!) -- ein Open-Source AI Hedge Fund mit 6 Agenten
- Bekannt in der AI-Finance-Community, gestarrt von Chip Huyen (AI Engineering Autorin), Didier Lopes (OpenBB Gruender), Junyang Lin (Alibaba Qwen)

### Das Geschaeftsmodell dahinter:
Dexter ist KOSTENLOS und Open Source. Die Monetarisierung laeuft ueber **financialdatasets.ai** -- die kostenpflichtige API, die Dexter als Datenquelle braucht. Klassisches Open-Source + API-Monetarisierung Pattern.

---

## ARCHITEKTUR

### Multi-Agent System (4 Agenten)

```
User Query: "Ist Apple unterbewertet?"
         |
         v
+------------------+
| PLANNING AGENT   |  Zerlegt komplexe Frage in einzelne Tasks
+------------------+  z.B.: Aktienkurs holen, P/E berechnen, Branchenschnitt vergleichen
         |
         v
+------------------+
| ACTION AGENT     |  Fuehrt Tasks aus, ruft Tools/APIs auf
+------------------+  Financial Datasets API, SEC Filings, Web Search
         |
         v
+------------------+
| VALIDATION AGENT |  Prueft Ergebnisse auf Konsistenz & Logik
+------------------+  Zeitraeume korrekt? Zahlen plausibel? Aepfel mit Aepfeln?
         |
         v
+------------------+
| ANSWER AGENT     |  Synthetisiert alles zu einer finalen Analyse
+------------------+
```

### Kernkonzept: Self-Validation
Das ist der USP von Dexter gegenueber anderen AI-Agents:
- Die meisten Agents (AutoGPT, etc.) haben KEINE domain-spezifische Validierung
- Dexter hat einen eigenen Validation Agent der prueft:
  - Stimmen die Zeitraeume ueberein?
  - Sind die Zahlen logisch konsistent?
  - Werden gleiche Metriken verglichen?
- Erst NACH Validierung wird die finale Antwort generiert
- Loest das "Trust Problem" bei AI-Finanzanalyse

### Safety Features
- Loop Detection: Verhindert endlose Reasoning-Loops
- Step Limits: Max 10 Iterationen pro Query
- Circuit Breakers: Schutz vor API-Budget-Verschwendung

### Scratchpad System
- Speichert alle Tool-Ergebnisse als JSONL in `.dexter/scratchpad/`
- Vollstaendige Transparenz: Jeder Schritt nachvollziehbar
- Token-Management: Aelteste Ergebnisse werden bei Token-Limit geloescht

---

## FEATURES

### Tools die Dexter nutzt:
| Tool | Funktion |
|------|----------|
| `financial_search` | Primaer-Tool fuer alle Finanzdaten (Preise, Metriken, Filings) |
| `financial_metrics` | Direkte Metrik-Abfragen (Revenue, Market Cap, etc.) |
| `read_filings` | SEC Filings lesen (10-K, 10-Q, 8-K) |
| `web_search` | Web-Suche via Exa oder Tavily |
| `browser` | Playwright-basiertes Web Scraping |
| `skill` | Ausfuehrung von SKILL.md-definierten Workflows (z.B. DCF-Bewertung) |

### Unterstuetzte LLM-Provider:
- OpenAI (Default)
- Anthropic (Claude)
- Google (Gemini)
- xAI (Grok)
- OpenRouter
- **Ollama (Local!)** -- wichtig fuer Maurice!

### Datenquellen (via financialdatasets.ai):
- 30.000+ Ticker, 30+ Jahre Historie
- Income Statements, Balance Sheets, Cash Flow Statements
- SEC Filings (10-K, 10-Q, 8-K)
- Insider Trades, Institutional Ownership
- Echtzeit + historische Aktienkurse
- Segmentierte Finanzdaten

### Beispiel-Queries:
- "Was war Apples Revenue-Wachstum in den letzten 4 Quartalen?"
- "Ist Tesla unterbewertet basierend auf P/E, Debt-to-Equity?"
- "Vergleiche die Margen von NVIDIA vs AMD"
- "Fuehre eine DCF-Bewertung fuer Microsoft durch"

### Kosten pro Query:
- Financial Datasets API: Kostenlos fuer moderate Nutzung (AAPL, MSFT, NVDA, TSLA komplett gratis)
- LLM-Kosten: $0.10 - $0.50 pro Analyse mit GPT-4
- Mit Ollama: $0.00 (lokal!)

---

## TECH STACK

| Komponente | Technologie |
|-----------|-------------|
| Runtime | Bun v1.0+ |
| Sprache | TypeScript |
| CLI Framework | Ink (React fuer CLI) |
| LLM Orchestration | LangChain |
| Web Scraping | Playwright |
| Evaluation | Jest + LangSmith |
| Daten-API | financialdatasets.ai REST API |
| Web Search | Exa (primaer) / Tavily (fallback) |

### Projektstruktur:
```
dexter/
  src/
    agent/
      agent.ts       # Core Agent Loop (max 10 Iterationen)
      scratchpad.ts   # Ergebnis-Speicher (JSONL)
    tools/
      registry.ts     # Tool-Registrierung
    evals/
      run.ts          # Evaluation Suite
  .dexter/
    scratchpad/       # Query-Logs mit Timestamps
```

---

## WAS KOENNEN WIR LERNEN? (fuer Maurice's AI Empire)

### 1. Das "Claude Code fuer X" Pattern
Dexter ist im Kern ein NISCHEN-AGENT. Er nimmt das Claude Code Konzept (autonomer Agent mit Tools) und spezialisiert es auf EINE Domain (Finance). Das ist exakt replizierbar:

**"Claude Code, aber fuer Brandmeldeanlagen"** = BMA-Agent der:
- Normen liest und interpretiert (DIN 14675, VDE 0833)
- Anlagenplanung validiert
- Stoerungsmeldungen analysiert
- Wartungsprotokolle generiert
- Preiskalkulation automatisiert

### 2. Multi-Agent mit Validation
Das 4-Agenten-Pattern (Plan -> Execute -> Validate -> Answer) ist Gold wert:
- **BMA-Planner:** Zerlegt Kundenanfrage in Teilaufgaben
- **BMA-Executor:** Fuehrt Berechnungen/Recherchen durch
- **BMA-Validator:** Prueft gegen Normen und Vorschriften
- **BMA-Answerer:** Erstellt finales Dokument/Angebot

### 3. Open Source + API Monetarisierung
Virat's Trick: Dexter ist gratis, aber die DATEN kosten Geld (financialdatasets.ai). Maurice kann das gleiche machen:
- BMA-Agent: Open Source (Community + Reputation)
- BMA-Datenbank (Normen, Produktdaten, Preislisten): Bezahl-API
- Oder: Freemium SaaS mit Premium-Features

### 4. Scratchpad = Transparenz = Vertrauen
In der BMA-Branche ist Nachvollziehbarkeit PFLICHT (Dokumentationspflicht!). Ein Scratchpad-System das jeden Schritt loggt ist perfekt fuer:
- Pruefprotokolle
- Abnahmedokumentation
- Behoerden-Nachweise

### 5. Ollama-Support = Datenschutz
Dexter unterstuetzt Ollama fuer lokale LLM-Ausfuehrung. Fuer BMA-Daten (Gebaeudeplaene, Sicherheitssysteme) ist das KRITISCH -- keine Kundendaten in die Cloud!

### 6. Evaluation Suite
Dexter hat eine eingebaute Eval-Suite die den Agent gegen Finanzfragen testet. Fuer einen BMA-Agent braeuchte man:
- Testfaelle aus echten Projekten
- Normkonformitaets-Checks
- Kalkulationsgenauigkeits-Tests

---

## MONETARISIERUNG (wie kann Maurice aehnliche Nischen-AI-Tools bauen)

### Direkte Anwendung: "BMA-Dexter"
Ein autonomer Agent fuer Brandmeldeanlangen-Planung und -Wartung:

| Feature | Zielgruppe | Preis |
|---------|-----------|-------|
| Normen-Checker | Errichter, Planer | 49 EUR/Monat |
| Anlagen-Kalkulator | Errichterfirmen | 99 EUR/Monat |
| Wartungsplaner | Betreiber | 29 EUR/Monat |
| Stoerungsanalyse-AI | Servicetechniker | 79 EUR/Monat |
| Komplett-Suite | Unternehmen | 299 EUR/Monat |

### Monetarisierung nach Virat's Modell:
1. **Open Source Agent** (kostenlos) -> Community aufbauen
2. **Premium API** (BMA-Normen-Datenbank, Produktkataloge) -> Recurring Revenue
3. **SaaS Dashboard** -> Fuer nicht-technische Nutzer
4. **Consulting/Training** -> BMA + AI Expertise verkaufen

### Marktpotenzial:
- Deutschland: ~5.000 Errichterfirmen fuer BMA
- DACH-Region: ~8.000 Firmen
- Bei 299 EUR/Monat und 500 Kunden = 1.8 Mio EUR/Jahr ARR
- Skalierung auf Gebaeudetechnik allgemein: 10x Markt

### Weitere Nischen nach dem "Claude Code fuer X" Pattern:
- "Claude Code fuer Elektroinstallation" (VDE-Normen)
- "Claude Code fuer Gebaeudeautomation" (KNX, BACnet)
- "Claude Code fuer SHK" (Sanitaer, Heizung, Klima)
- "Claude Code fuer Aufzuege" (TUeV-Pruefungen)
- Jede regulierte Branche mit Dokumentationspflicht ist ein Kandidat!

---

## KEY TAKEAWAY

### Dexter beweist 3 Dinge:

1. **Nischen-AI-Agents sind der Weg zu Geld.** Nicht "General Purpose AI" sondern "Claude Code fuer [BRANCHE]" ist die Goldgrube. Dexter hat 11.600+ Stars weil es EIN Problem hervorragend loest.

2. **Open Source + API = perfektes Geschaeftsmodell.** Der Agent ist gratis (Marketing + Community), die Daten kosten Geld (Revenue). Maurice kann das 1:1 auf BMA uebertragen.

3. **Validation Agent = Vertrauenswuerdigkeit.** In regulierten Branchen (Finance, BMA, Medizin) ist Selbst-Validierung der Schluessel. Ein BMA-Agent der seine eigenen Ergebnisse gegen DIN-Normen prueft ist 10x wertvoller als einer ohne.

### Sofort-Aktion fuer Maurice:
- [ ] Dexter klonen und lokal testen (`git clone + bun install`)
- [ ] Architektur studieren (nur ~200 Zeilen Kern-Code!)
- [ ] "BMA-Dexter" Prototyp: Gleiche 4-Agent-Architektur, aber mit BMA-Normen statt Finanzdaten
- [ ] BMA-Normen-API aufbauen (DIN 14675 als strukturierte Datenbank)
- [ ] MVP in 2 Wochen moeglich mit Dexter als Template

### Verbindung zu OpenClaw:
Dexter ist NICHT direkt mit OpenClaw verbunden. Die Bezeichnung "OpenClaw and Claude Code for finance" bezieht sich darauf, dass Dexter konzeptionell das gleiche Prinzip nutzt wie Claude Code: Ein autonomer Agent der plant, ausfuehrt, und validiert. Maurice's OpenClaw-Architektur (Event Broker + Model Router + Swarm) koennte als BACKEND fuer einen BMA-Dexter dienen:
- OpenClaw Event Broker = Task Queue fuer BMA-Queries
- OpenClaw Model Router = Ollama fuer lokale Ausfuehrung (Datenschutz!)
- OpenClaw Swarm = Parallele Verarbeitung mehrerer Kundenanfragen

---

## QUELLEN
- https://github.com/virattt/dexter
- https://github.com/virattt/ai-hedge-fund
- https://yuv.ai/blog/dexter
- https://www.financialdatasets.ai
- https://docs.financialdatasets.ai/introduction
- https://x.com/virattt
