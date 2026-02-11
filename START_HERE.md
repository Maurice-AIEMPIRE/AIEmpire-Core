# AI EMPIRE — START HERE

## Schnellstart (2 Minuten)

### 1. Ollama starten (GRATIS AI)
```bash
# Terminal 1: Ollama starten
ollama serve

# Terminal 2: Model installieren (einmalig, ~4GB)
ollama pull qwen2.5-coder:7b
```

### 2. System testen
```bash
cd ~/AIEmpire-Core
python3 test_freeware.py
```
Das testet ALLES: Ollama, Provider Chain, Agents, Knowledge Store.

### 3. System Dashboard
```bash
python3 empire_boot.py
```

### 4. AI fragen (kostenlos!)
```bash
python3 empire_boot.py ask "Erklaere mir AI Agents in 3 Saetzen"
```

### 5. Agents starten
```bash
python3 -m antigravity.agent_orchestrator auto
```

---

## Fix: Antigravity Google Error

Der Fehler `"Invalid project resource name projects/"` kommt weil Google Antigravity (Browser-Tool) kein Projekt konfiguriert hat.

### Fix in 30 Sekunden:
```bash
# 1. Google Cloud SDK installieren (falls noch nicht)
brew install google-cloud-sdk

# 2. Projekt setzen
gcloud config set project ai-empire-486415

# 3. Login (einmalig)
gcloud auth login
gcloud auth application-default login
```

### Wenn du KEIN Google Cloud willst:
Kein Problem! Das System funktioniert 100% OHNE Google.
Ollama ist deine lokale AI — kostenlos und unbegrenzt.

---

## Architektur

```
empire_boot.py          → Haupteinstieg (Status, Start, Stop, Repair)
empire_engine.py        → Revenue Machine (Scan, Produce, Distribute)
test_freeware.py        → Testet ALLES kostenlos mit Ollama

antigravity/
  provider_chain.py     → Smart AI Routing (Ollama→Kimi→Gemini→OpenRouter)
  agent_orchestrator.py → Multi-Agent System
  config.py             → Zentrale Konfiguration
  knowledge_store.py    → Persistentes Wissen
  empire_bridge.py      → Verbindet alle Systeme
```

## Taeglich nutzen

```bash
python3 empire_boot.py                   # Status
python3 empire_boot.py ask "..."         # AI fragen (kostenlos)
python3 empire_engine.py auto            # Autonomer Zyklus
python3 empire_boot.py repair            # System reparieren
```
