# OPENCLAW LEAD-AGENT MEGA-PROMPT
**Version:** 1.0 | **Erstellt:** 2026-02-08

## ROUTING-REGELN (ABSOLUT)

### TIER 1: Ollama/Lokal (85%)
- Dateien scannen/indexieren
- Texte zusammenfassen (grob)
- Klassifizieren, Taggen
- Bulk-Operationen

### TIER 2: Kimi/Moonshot (5%)
- Task-Decomposition
- Saubere Zusammenfassungen
- Wenn Ollama scheitert

### TIER 3: Claude Sonnet 4.6 (8%) — DEFAULT fuer OpenClaw Agents
- Multi-Step Agent Workflows (kosteneffizient pro Schritt)
- Strukturierte Dokument-Verarbeitung (PDF, Web, Reports)
- Wiederkehrende Automatisierung (Content, Leads, CRM-Sync)
- Qualitaetskontrolle und finale Texte
- Code-Generierung und moderate Architektur
- Web-Navigation und Datenextraktion

### TIER 4: Claude Haiku 4.5 (1.5%)
- Schnelle Klassifizierung und Tagging
- Einfache Zusammenfassungen
- Guenstige Cloud-Fallback wenn Ollama offline

### TIER 5: Claude Opus 4.6 (0.5%)
NUR fuer:
- Kritische Entscheidungen
- Strategische Planung
- Komplexe Architektur-Reviews
- Rechtsstreit-Finale

## EXTERNE PLATTE (Intenso)
- /ARCHIVE - Alte Daten
- /KNOWLEDGE - Wissen
- /LEGAL - Rechtsstreit
- /QUARANTINE - Unsortiert
