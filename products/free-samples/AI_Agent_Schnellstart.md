# KOSTENLOSE PROBE: AI Agent Schnellstart
## Ollama + Python in 15 Minuten | Aus dem AI Setup Blueprint

> Von Maurice Pfeifer — baut AI-Systeme die 24/7 autonom arbeiten

---

## Schritt 1: Ollama installieren (2 Minuten)

```bash
# Linux/Mac — ein Befehl:
curl -fsSL https://ollama.ai/install.sh | sh

# Pruefen ob es laeuft:
ollama --version
```

## Schritt 2: Erstes AI-Modell laden (5 Minuten)

```bash
# Lade ein schnelles, kostenloses Modell:
ollama pull qwen2.5-coder:7b

# Teste es sofort:
ollama run qwen2.5-coder:7b "Schreibe eine Python-Funktion die Primzahlen findet"
```

## Schritt 3: Python-Anbindung (3 Minuten)

```bash
pip install httpx
```

```python
import httpx

def frag_ollama(frage: str) -> str:
    """Schicke eine Frage an dein lokales AI-Modell."""
    response = httpx.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5-coder:7b",
            "prompt": frage,
            "stream": False
        },
        timeout=120
    )
    return response.json()["response"]

# Teste es:
antwort = frag_ollama("Was ist eine Brandmeldeanlage?")
print(antwort)
```

## Schritt 4: Dein erster Agent (5 Minuten)

```python
import httpx

class MiniAgent:
    """Ein minimaler AI-Agent der Aufgaben erledigt."""

    def __init__(self, name: str, rolle: str):
        self.name = name
        self.rolle = rolle

    def ausfuehren(self, aufgabe: str) -> str:
        prompt = f"Du bist {self.name}, ein {self.rolle}. Aufgabe: {aufgabe}"
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5-coder:7b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        return response.json()["response"]

# Erstelle deinen ersten Agent:
agent = MiniAgent("Max", "Python-Entwickler")
ergebnis = agent.ausfuehren("Schreibe eine TODO-App mit Flask")
print(ergebnis)
```

**Fertig!** Du hast gerade deinen ersten AI-Agenten gebaut. Lokal, kostenlos, in 15 Minuten.

---

**Das war nur der Anfang.**

Das vollstaendige **AI Setup Blueprint** (EUR 47) enthaelt:

- 4 Module mit Schritt-fuer-Schritt Anleitungen
- 10 fertige Agent-Templates (Copy-Paste)
- Multi-Agent System aufbauen (Agents die zusammenarbeiten)
- Automatisierte Workflows (Content, Recherche, Code-Review)
- Bonus: 15 Automatisierungs-Ideen die sofort Geld verdienen
- Alles mit kostenlosen, lokalen Modellen (kein API-Key noetig!)

---

## Komplettes Blueprint holen: EUR 47

Von der Installation bis zum produktiven Multi-Agent System.

---

*Maurice Pfeifer — Baut AI-Systeme mit 100+ Agents in Produktion*
*Mehr auf X: @MauricePfeifer*
