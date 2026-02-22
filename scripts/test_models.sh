#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# AIEmpire — Model Route Diagnostics
# Tests Ollama direct + LiteLLM proxy + all OpenClaw aliases
# Run this FIRST when models fail!
# ═══════════════════════════════════════════════════════════════

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

OLLAMA_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
LITELLM_URL="${LITELLM_PROXY_URL:-http://127.0.0.1:4000}"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  AIEmpire Model Route Diagnostics${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# ─── Helper: test a model endpoint ───────────────────────────
test_model() {
    local label="$1"
    local url="$2"
    local model="$3"
    local timeout="${4:-15}"

    local response
    response=$(curl -s --max-time "$timeout" -w "\n%{http_code}" \
        -X POST "$url/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ollama-local" \
        -d "{
            \"model\": \"$model\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Say OK\"}],
            \"max_tokens\": 5,
            \"temperature\": 0
        }" 2>/dev/null)

    local http_code
    http_code=$(echo "$response" | tail -1)
    local body
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        local content
        content=$(echo "$body" | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    print(d['choices'][0]['message']['content'][:50])
except: print('OK (parsed)')
" 2>/dev/null)
        echo -e "  ${GREEN}✓${NC} ${label} → ${content}"
        return 0
    else
        local error
        error=$(echo "$body" | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    e=d.get('error',{})
    if isinstance(e,dict): print(e.get('message','HTTP $http_code')[:60])
    else: print(str(e)[:60])
except: print('HTTP $http_code')
" 2>/dev/null)
        echo -e "  ${RED}✗${NC} ${label} → ${error:-HTTP $http_code}"
        return 1
    fi
}

passed=0
failed=0

# ─── 1. Ollama Direct ────────────────────────────────────────
echo -e "${YELLOW}[1/4] Ollama Direct ($OLLAMA_URL)${NC}"

if curl -s --max-time 3 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Ollama API erreichbar"

    # List installed models
    models=$(curl -s "$OLLAMA_URL/api/tags" 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    for m in d.get('models',[]):
        size_gb = m.get('size',0)/1024/1024/1024
        print(f\"    {m['name']} ({size_gb:.1f}GB)\")
except: pass
" 2>/dev/null)

    if [ -n "$models" ]; then
        echo -e "  Installierte Modelle:"
        echo "$models"
    else
        echo -e "  ${YELLOW}~${NC} Keine Modelle installiert!"
        echo -e "    ${YELLOW}→ ollama pull qwen2.5-coder:14b${NC}"
    fi
else
    echo -e "  ${RED}✗${NC} Ollama NICHT erreichbar!"
    echo -e "    ${YELLOW}→ Starte: ollama serve${NC}"
    ((failed++))
fi

# ─── 2. LiteLLM Proxy ────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/4] LiteLLM Proxy ($LITELLM_URL)${NC}"

if curl -s --max-time 3 "$LITELLM_URL/health" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} LiteLLM Proxy erreichbar"

    # List available models
    proxy_models=$(curl -s "$LITELLM_URL/v1/models" \
        -H "Authorization: Bearer ollama-local" 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    seen=set()
    for m in d.get('data',[]):
        name=m['id']
        if name not in seen:
            seen.add(name)
            print(f'    {name}')
except: pass
" 2>/dev/null)

    if [ -n "$proxy_models" ]; then
        echo -e "  Verfuegbare Modelle via Proxy:"
        echo "$proxy_models"
    fi
else
    echo -e "  ${RED}✗${NC} LiteLLM Proxy NICHT erreichbar!"
    echo -e "    ${YELLOW}→ docker compose -f openclaw-config/docker-compose.yaml up -d litellm${NC}"
    ((failed++))
fi

# ─── 3. Real Model Tests (Ollama Direct) ─────────────────────
echo ""
echo -e "${YELLOW}[3/4] Modell-Tests (Ollama direkt)${NC}"

for model in "qwen2.5-coder:14b" "qwen2.5-coder:7b" "deepseek-r1:7b" "codellama:7b" "mistral:7b"; do
    if test_model "$model" "$OLLAMA_URL" "$model" 20; then
        ((passed++))
    else
        ((failed++))
    fi
done

# ─── 4. OpenClaw Alias Tests (via LiteLLM) ───────────────────
echo ""
echo -e "${YELLOW}[4/4] OpenClaw-Alias Tests (via LiteLLM Proxy)${NC}"

if curl -s --max-time 3 "$LITELLM_URL/health" >/dev/null 2>&1; then
    for model in "ollama/qwen3.5:cloud" "ollama/qwen3-nothinkin:latest" "ollama/qwen3:8b" "ollama/qwen3-coder:latest" "qwen-14b" "qwen-7b" "deepseek-r1"; do
        if test_model "$model" "$LITELLM_URL" "$model" 20; then
            ((passed++))
        else
            ((failed++))
        fi
    done
else
    echo -e "  ${YELLOW}~${NC} LiteLLM offline — Alias-Tests uebersprungen"
fi

# ─── Summary ─────────────────────────────────────────────────
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
total=$((passed + failed))
if [ "$failed" -eq 0 ]; then
    echo -e "  ${GREEN}ALLE TESTS BESTANDEN ($passed/$total)${NC}"
else
    echo -e "  ${YELLOW}ERGEBNIS: $passed bestanden, $failed fehlgeschlagen${NC}"
fi
echo ""

# ─── Quick Fix Hints ─────────────────────────────────────────
if [ "$failed" -gt 0 ]; then
    echo -e "${YELLOW}Quick Fixes:${NC}"
    echo "  1. Ollama starten:    ollama serve"
    echo "  2. Modell pullen:     ollama pull qwen2.5-coder:14b"
    echo "  3. LiteLLM starten:   docker compose -f openclaw-config/docker-compose.yaml up -d"
    echo "  4. Native Ollama:     export OLLAMA_API_URL=http://127.0.0.1:11434"
    echo "  5. Docker Ollama:     export OLLAMA_API_URL=http://ollama:11434"
    echo "  6. Mac→Docker:        export OLLAMA_API_URL=http://host.docker.internal:11434"
    echo ""
fi
