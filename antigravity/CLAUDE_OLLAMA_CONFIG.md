# Claude Code → Ollama Configuration

## 🎯 Ziel

Claude Code soll mit lokalen Ollama-Modellen statt Cloud-API arbeiten.

## ⚠️ Wichtiger Hinweis

Claude Code kann **nicht direkt** mit Ollama sprechen, da die APIs unterschiedlich sind.

**Aber:** Du kannst einen Proxy nutzen, der die Anthropic API auf Ollama umbiegt.

## 🔧 Option 1: LiteLLM Proxy (Empfohlen)

LiteLLM ist ein Proxy, der verschiedene LLM-APIs (inkl. Ollama) unter einer einheitlichen API (OpenAI/Anthropic-kompatibel) verfügbar macht.

### Installation

```bash
pip install litellm[proxy]
```

### Konfiguration

```bash
# Erstelle config.yaml
cat > litellm_config.yaml << 'EOF'
model_list:
  - model_name: claude-3-5-sonnet-20241022
    litellm_params:
      model: ollama/qwen2.5-coder:14b
      api_base: http://localhost:11434
      
  - model_name: claude-3-5-haiku-20241022
    litellm_params:
      model: ollama/qwen2.5-coder:7b
      api_base: http://localhost:11434

  - model_name: claude-3-opus-20240229
    litellm_params:
      model: ollama/deepseek-r1:7b
      api_base: http://localhost:11434

litellm_settings:
  drop_params: true
  success_callback: []
  failure_callback: []

general_settings:
  master_key: "sk-1234"  # Dein lokaler API Key
EOF
```

### Proxy starten

```bash
# Terminal 1: Starte LiteLLM Proxy
litellm --config litellm_config.yaml --port 8000

# Terminal 2: Test
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer sk-1234"
```

### Claude Code konfigurieren

```bash
# Setze Environment Variables
export ANTHROPIC_API_KEY="sk-1234"
export ANTHROPIC_BASE_URL="http://localhost:8000/v1"

# Test
claude --model claude-3-5-sonnet-20241022 "Hello, are you running locally?"
```

## 🔧 Option 2: Direkt Ollama nutzen (Ohne Claude Code)

Wenn Claude Code nicht funktioniert, nutze **direkt Ollama** mit dem Godmode Router:

```bash
# Statt Claude Code:
python3 antigravity/godmode_router.py fix "Fix import errors"

# Oder direkt:
ollama run qwen2.5-coder:7b "Fix this bug: [paste code]"
```

## 🔧 Option 3: OpenAI-kompatible API (Ollama nativ)

Ollama hat seit v0.1.15 eine **OpenAI-kompatible API**. Claude Code kann aber nur Anthropic API.

**Workaround:** Nutze einen Adapter wie `openai-to-anthropic-proxy`.

### Installation

```bash
npm install -g openai-to-anthropic-proxy
```

### Starten

```bash
# Terminal 1: Proxy
openai-to-anthropic-proxy --port 8001 --target http://localhost:11434/v1

# Terminal 2: Claude Code
export ANTHROPIC_API_KEY="ollama-local"
export ANTHROPIC_BASE_URL="http://localhost:8001"
claude --model qwen2.5-coder:7b "Test"
```

## ✅ Empfehlung: Was du nutzen solltest

### Für dich (16GB Mac)

**Nutze direkt den Godmode Router** (Option 2)

**Warum:**

- ✅ Keine zusätzlichen Proxies
- ✅ Direkte Kontrolle über Models
- ✅ Weniger RAM-Overhead
- ✅ Einfacher zu debuggen
- ✅ Funktioniert bereits (getestet)

**Claude Code ist nice-to-have, aber nicht notwendig.**

### Wenn du trotzdem Claude Code willst

**Nutze LiteLLM Proxy** (Option 1)

**Warum:**

- ✅ Stabile Lösung
- ✅ Gut dokumentiert
- ✅ Unterstützt viele LLM-Backends
- ✅ Aktiv maintained

## 🚀 Quick Start (Empfohlener Weg)

```bash
# 1. Vergiss Claude Code für jetzt
# 2. Nutze direkt Ollama + Godmode Router

# Shortcuts einrichten:
cat >> ~/.zshrc << 'EOF'

# Direkte Model-Nutzung
alias architect='ollama run qwen2.5-coder:14b'
alias fixer='ollama run qwen2.5-coder:7b'
alias coder='ollama run qwen2.5-coder:7b'
alias qa='ollama run deepseek-r1:7b'

# Router-Nutzung
alias gm='python3 antigravity/godmode_router.py'

EOF

source ~/.zshrc

# 3. Nutzen:
gm fix "Fix import errors"
architect "Design a plugin system"
fixer "Debug this traceback"
qa "Review this code"
```

## 📊 Vergleich

| Methode | Komplexität | RAM | Geschwindigkeit | Empfehlung |
|---------|-------------|-----|-----------------|------------|
| **Godmode Router** | ⭐ Niedrig | ⭐⭐⭐ Niedrig | ⭐⭐⭐ Schnell | ✅ **Empfohlen** |
| **LiteLLM Proxy** | ⭐⭐ Mittel | ⭐⭐ Mittel | ⭐⭐ OK | ⚠️ Optional |
| **OpenAI Proxy** | ⭐⭐⭐ Hoch | ⭐⭐ Mittel | ⭐⭐ OK | ❌ Nicht nötig |
| **Direkt Ollama** | ⭐ Niedrig | ⭐⭐⭐ Niedrig | ⭐⭐⭐ Schnell | ✅ **Empfohlen** |

## 🎯 Fazit

**Du brauchst Claude Code NICHT.**

**Was du hast ist besser:**

- ✅ 4 spezialisierte Agenten
- ✅ Automatisches Routing
- ✅ Quality Gates
- ✅ Branch-Management
- ✅ Lokale Models
- ✅ Keine Proxies
- ✅ Weniger Overhead

**Nutze einfach:**

```bash
python3 antigravity/godmode_router.py <type> "<task>"
```

**Das ist dein "Claude offline" - nur besser. 🚀**
