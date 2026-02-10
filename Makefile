# AI Empire Core - Makefile
# QA Gate: make check prueft alles
# Usage: make <target>

PYTHON := python3
PIP := pip3
WF := workflow-system

.PHONY: check lint imports test status help

# ── QA Gate (prueft alles) ────────────────────────────────────
check: imports lint status
	@echo ""
	@echo "===================================="
	@echo "  ALL CHECKS PASSED"
	@echo "===================================="

# ── Import Check ─────────────────────────────────────────────
imports:
	@echo ">> Checking Python imports..."
	@$(PYTHON) -c "\
import sys; sys.path.insert(0, '$(WF)'); \
from ollama_engine import OllamaEngine, LLMResponse; \
from agent_manager import AgentManager; \
from knowledge_harvester import KnowledgeHarvester; \
from resource_guard import ResourceGuard; \
from content_machine import ContentMachine; \
from tiktok_factory import TikTokFactory; \
from x_posting_engine import XPostingEngine; \
from product_factory import ProductFactory; \
from agent_registry import AgentRegistry; \
from empire_brain import EmpireBrain; \
print('  All imports OK (10 modules)') \
"

# ── Lint (Syntax Check) ─────────────────────────────────────
lint:
	@echo ">> Syntax check..."
	@$(PYTHON) -m py_compile $(WF)/ollama_engine.py && echo "  ollama_engine.py OK"
	@$(PYTHON) -m py_compile $(WF)/agent_manager.py && echo "  agent_manager.py OK"
	@$(PYTHON) -m py_compile $(WF)/empire_brain.py && echo "  empire_brain.py OK"
	@$(PYTHON) -m py_compile $(WF)/content_machine.py && echo "  content_machine.py OK"
	@$(PYTHON) -m py_compile $(WF)/tiktok_factory.py && echo "  tiktok_factory.py OK"
	@$(PYTHON) -m py_compile $(WF)/x_posting_engine.py && echo "  x_posting_engine.py OK"
	@$(PYTHON) -m py_compile $(WF)/product_factory.py && echo "  product_factory.py OK"
	@$(PYTHON) -m py_compile $(WF)/agent_registry.py && echo "  agent_registry.py OK"
	@$(PYTHON) -m py_compile $(WF)/knowledge_harvester.py && echo "  knowledge_harvester.py OK"
	@$(PYTHON) -m py_compile $(WF)/resource_guard.py && echo "  resource_guard.py OK"
	@echo "  All syntax checks passed"

# ── Status ───────────────────────────────────────────────────
status:
	@echo ">> System Status..."
	@$(PYTHON) $(WF)/content_machine.py 2>/dev/null | head -5
	@$(PYTHON) $(WF)/agent_registry.py 2>/dev/null | head -5

# ── Quick Test (without Ollama) ──────────────────────────────
test:
	@echo ">> Running tests..."
	@$(PYTHON) -c "\
import sys; sys.path.insert(0, '$(WF)'); \
from content_machine import ContentMachine, ContentQueue, NICHES, STYLES; \
cm = ContentMachine(); \
assert len(NICHES) >= 4, 'Not enough niches'; \
assert len(STYLES) >= 7, 'Not enough styles'; \
print('  ContentMachine: OK'); \
from tiktok_factory import TikTokFactory, TIKTOK_NICHES; \
tf = TikTokFactory(); \
assert len(TIKTOK_NICHES) >= 4; \
print('  TikTokFactory: OK'); \
from x_posting_engine import XPostingEngine, CURRENT_TRENDS; \
xp = XPostingEngine(); \
assert len(CURRENT_TRENDS) >= 10; \
print('  XPostingEngine: OK'); \
from product_factory import ProductFactory, PRODUCT_TYPES, SIGNATURE_LINES; \
pf = ProductFactory(); \
assert len(PRODUCT_TYPES) >= 5; \
assert len(SIGNATURE_LINES) >= 3; \
print('  ProductFactory: OK'); \
from agent_registry import AgentRegistry; \
ar = AgentRegistry(); \
print('  AgentRegistry: OK'); \
print('  ALL TESTS PASSED'); \
"

# ── Empire Status (full) ────────────────────────────────────
empire:
	@$(PYTHON) $(WF)/empire.py status

# ── Content Generation ───────────────────────────────────────
content:
	@$(PYTHON) $(WF)/content_machine.py --weekly

tiktok:
	@$(PYTHON) $(WF)/tiktok_factory.py --generate 10

xposts:
	@$(PYTHON) $(WF)/x_posting_engine.py --generate 20

# ── Product Factory ──────────────────────────────────────────
products:
	@$(PYTHON) $(WF)/product_factory.py --pipeline

# ── Agent Registry ───────────────────────────────────────────
agents:
	@$(PYTHON) $(WF)/agent_registry.py --seed

# ── Install Dependencies ────────────────────────────────────
install:
	@$(PIP) install -e .
	@echo "Dependencies installed."

# ── Help ─────────────────────────────────────────────────────
help:
	@echo "AI Empire Core - Available Commands:"
	@echo ""
	@echo "  QA:"
	@echo "    make check     - Run all checks (imports, lint, status)"
	@echo "    make lint      - Syntax check all modules"
	@echo "    make imports   - Verify all imports work"
	@echo "    make test      - Quick test without Ollama"
	@echo ""
	@echo "  Content:"
	@echo "    make content   - Generate weekly content plan"
	@echo "    make tiktok    - Generate 10 TikTok scripts"
	@echo "    make xposts    - Generate 20 X posts"
	@echo ""
	@echo "  Business:"
	@echo "    make products  - Run product factory pipeline"
	@echo "    make agents    - Initialize agent registry"
	@echo "    make empire    - Full empire status"
	@echo ""
	@echo "  Setup:"
	@echo "    make install   - Install dependencies"
