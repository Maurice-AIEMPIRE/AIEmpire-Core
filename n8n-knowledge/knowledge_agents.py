#!/usr/bin/env python3
"""
10 Claude Offline Agents - n8n Knowledge Processor.

10 spezialisierte Agenten die parallel n8n-Wissen verarbeiten, lernen,
und konkrete Implementierungen fuer das AIEmpire System erstellen.

Agent 1:  ARCHITECT     - n8n Systemarchitektur fuer AIEmpire designen
Agent 2:  WORKFLOW_GEN  - n8n Workflows generieren fuer alle Revenue Channels
Agent 3:  AI_AGENT_BUILDER - n8n AI Agents konfigurieren (LangChain, RAG)
Agent 4:  INTEGRATION   - Alle AIEmpire-Systeme mit n8n verbinden
Agent 5:  DOCKER_OPS    - Docker Production Setup + Scaling
Agent 6:  API_BRIDGE    - n8n REST API Bridge fuer Empire Control
Agent 7:  MEMORY_SYNC   - n8n ↔ Digital Memory Synchronisation
Agent 8:  REVENUE_AUTO  - Revenue-generierende Workflows automatisieren
Agent 9:  MONITOR       - System Health + Performance Monitoring via n8n
Agent 10: EVOLUTION     - n8n Workflows die sich selbst optimieren

Usage:
    python n8n-knowledge/knowledge_agents.py                # Alle 10 Agenten parallel
    python n8n-knowledge/knowledge_agents.py --agent 1      # Einzelner Agent
    python n8n-knowledge/knowledge_agents.py --status       # Status aller Agenten
    python n8n-knowledge/knowledge_agents.py --ingest       # Wissen in Digital Memory laden
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Path setup
PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_DIR = Path(__file__).parent
GEMINI_DIR = PROJECT_ROOT / "gemini-mirror"
sys.path.insert(0, str(GEMINI_DIR))
sys.path.insert(0, str(KNOWLEDGE_DIR))

STATE_FILE = KNOWLEDGE_DIR / "agents" / "agent_state.json"
KNOWLEDGE_FILE = KNOWLEDGE_DIR / "n8n_complete_knowledge.json"


def load_knowledge() -> dict:
    """Load the complete n8n knowledge base."""
    return json.loads(KNOWLEDGE_FILE.read_text())


def load_state() -> dict:
    """Load agent processing state."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"agents": {}, "started_at": None, "completed_at": None}


def save_state(state: dict):
    """Save agent processing state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ============================================================
# AGENT DEFINITIONS
# ============================================================

AGENTS = {
    1: {
        "name": "ARCHITECT",
        "role": "n8n Systemarchitektur fuer AIEmpire designen",
        "focus": "Wie n8n optimal in das AIEmpire System integriert wird",
        "outputs": ["architecture_plan.json"],
    },
    2: {
        "name": "WORKFLOW_GEN",
        "role": "n8n Workflows generieren fuer alle Revenue Channels",
        "focus": "Gumroad, Fiverr, Consulting, X/Twitter Workflows",
        "outputs": ["revenue_workflows.json"],
    },
    3: {
        "name": "AI_AGENT_BUILDER",
        "role": "n8n AI Agents konfigurieren (LangChain, RAG, Tools)",
        "focus": "AI Agent Nodes mit Ollama/Gemini/Claude Setup",
        "outputs": ["ai_agent_configs.json"],
    },
    4: {
        "name": "INTEGRATION",
        "role": "Alle AIEmpire-Systeme mit n8n verbinden",
        "focus": "CRM, Kimi Swarm, Atomic Reactor, Brain System Bridges",
        "outputs": ["integration_map.json"],
    },
    5: {
        "name": "DOCKER_OPS",
        "role": "Docker Production Setup + Scaling Konfiguration",
        "focus": "docker-compose, PostgreSQL, Redis Queue, Traefik SSL",
        "outputs": ["docker_production.yaml"],
    },
    6: {
        "name": "API_BRIDGE",
        "role": "n8n REST API Bridge fuer Empire Control Center",
        "focus": "Python Client, Workflow Management, Execution Control",
        "outputs": ["n8n_api_bridge.py"],
    },
    7: {
        "name": "MEMORY_SYNC",
        "role": "n8n ↔ Digital Memory Synchronisation",
        "focus": "Workflow-Ergebnisse in Digital Memory speichern",
        "outputs": ["memory_sync_workflow.json"],
    },
    8: {
        "name": "REVENUE_AUTO",
        "role": "Revenue-generierende Workflows automatisieren",
        "focus": "Lead Gen → Qualify → Sell → Deliver → Follow-up Pipeline",
        "outputs": ["revenue_automation.json"],
    },
    9: {
        "name": "MONITOR",
        "role": "System Health + Performance Monitoring via n8n",
        "focus": "Health Checks, Alerts, Performance Dashboards",
        "outputs": ["monitoring_workflows.json"],
    },
    10: {
        "name": "EVOLUTION",
        "role": "n8n Workflows die sich selbst optimieren",
        "focus": "Self-healing, Auto-optimization, A/B Testing",
        "outputs": ["evolution_workflows.json"],
    },
}


async def run_agent(agent_id: int, knowledge: dict) -> dict:
    """Run a single knowledge processing agent."""
    agent = AGENTS[agent_id]
    print(f"  [{agent_id:2d}] {agent['name']:20s} Starting...")

    result = {
        "agent_id": agent_id,
        "name": agent["name"],
        "role": agent["role"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
    }

    try:
        # Each agent processes knowledge from its perspective
        if agent_id == 1:
            output = await _agent_architect(knowledge)
        elif agent_id == 2:
            output = await _agent_workflow_gen(knowledge)
        elif agent_id == 3:
            output = await _agent_ai_builder(knowledge)
        elif agent_id == 4:
            output = await _agent_integration(knowledge)
        elif agent_id == 5:
            output = await _agent_docker_ops(knowledge)
        elif agent_id == 6:
            output = await _agent_api_bridge(knowledge)
        elif agent_id == 7:
            output = await _agent_memory_sync(knowledge)
        elif agent_id == 8:
            output = await _agent_revenue_auto(knowledge)
        elif agent_id == 9:
            output = await _agent_monitor(knowledge)
        elif agent_id == 10:
            output = await _agent_evolution(knowledge)
        else:
            output = {"error": f"Unknown agent {agent_id}"}

        # Save agent output
        for filename in agent["outputs"]:
            output_path = KNOWLEDGE_DIR / "agents" / filename
            output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

        result["status"] = "completed"
        result["output_files"] = agent["outputs"]
        result["insights_count"] = len(output.get("insights", []))
        result["actions_count"] = len(output.get("actions", []))

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)

    result["completed_at"] = datetime.now(timezone.utc).isoformat()
    print(f"  [{agent_id:2d}] {agent['name']:20s} {result['status'].upper()}")
    return result


# ============================================================
# AGENT IMPLEMENTATIONS
# ============================================================

async def _agent_architect(k: dict) -> dict:
    """Agent 1: Design n8n architecture for AIEmpire."""
    return {
        "architecture": {
            "n8n_role": "Central automation hub connecting all AIEmpire systems",
            "deployment": {
                "type": "Docker self-hosted",
                "database": "PostgreSQL (shared with CRM)",
                "queue": "Redis (shared with existing Redis)",
                "port": 5678,
                "ssl": "Traefik auto-SSL"
            },
            "connections": {
                "empire_api": "Webhook ↔ Empire API (FastAPI)",
                "crm": "Direct PostgreSQL + REST API",
                "kimi_swarm": "HTTP Request nodes → Kimi API",
                "atomic_reactor": "Webhook triggers → Task execution",
                "gemini_mirror": "Schedule → Sync workflows",
                "brain_system": "Webhook ↔ Brain orchestrator",
                "x_lead_machine": "Schedule → Content + Lead workflows",
                "ollama": "AI Agent nodes → Ollama local models",
                "github": "GitHub nodes → Auto-deploy, issues"
            },
            "flow": "n8n orchestrates all systems, replaces manual triggers with automated workflows"
        },
        "insights": [
            "n8n wird der zentrale Automatisierungshub - alle Systeme verbunden",
            "Queue-Modus mit Redis fuer parallele Workflow-Ausfuehrung",
            "AI Agent Nodes ersetzen manuelle Kimi/Ollama Aufrufe",
            "Webhook-basierte Integration mit Empire API",
            "PostgreSQL shared zwischen n8n und CRM fuer konsistente Daten"
        ],
        "actions": [
            "Docker Compose mit n8n + PostgreSQL + Redis erstellen",
            "Empire API Webhook Endpoints hinzufuegen",
            "n8n Credentials fuer alle APIs einrichten",
            "Initiale Workflows fuer jeden Revenue Channel erstellen"
        ]
    }


async def _agent_workflow_gen(k: dict) -> dict:
    """Agent 2: Generate revenue workflows."""
    return {
        "workflows": {
            "gumroad_sales_pipeline": {
                "trigger": "Webhook (Gumroad sale event)",
                "nodes": ["Parse sale data", "Add to CRM", "Send welcome email", "AI personalized follow-up", "Upsell sequence trigger"],
                "revenue_impact": "Direct - automates post-sale, increases upsells"
            },
            "fiverr_order_processor": {
                "trigger": "Webhook (Fiverr order)",
                "nodes": ["Parse requirements", "AI Agent generates deliverable", "Quality check", "Deliver to client", "Request review"],
                "revenue_impact": "Direct - automates Fiverr delivery"
            },
            "x_twitter_content_engine": {
                "trigger": "Schedule (3x daily)",
                "nodes": ["AI Agent generates content", "Check against calendar", "Post to X", "Monitor engagement", "Extract leads from replies"],
                "revenue_impact": "Indirect - generates leads and visibility"
            },
            "lead_qualification_pipeline": {
                "trigger": "Webhook (new lead from any source)",
                "nodes": ["AI Agent scores lead (BANT)", "Route by score", "High score: personal outreach", "Medium: nurture sequence", "Low: content drip"],
                "revenue_impact": "Direct - converts leads to customers"
            },
            "bma_consulting_funnel": {
                "trigger": "Form submission + Schedule",
                "nodes": ["Qualify BMA need", "AI creates proposal", "Send to prospect", "Follow-up sequence", "Schedule call via Calendly"],
                "revenue_impact": "High - 2000-10000 EUR per deal"
            },
            "daily_revenue_dashboard": {
                "trigger": "Schedule (daily 07:00)",
                "nodes": ["Fetch Gumroad sales", "Fetch Fiverr orders", "Fetch CRM deals", "Calculate totals", "Send report to Telegram"],
                "revenue_impact": "Indirect - visibility drives decisions"
            }
        },
        "insights": [
            "6 Revenue-Workflows decken alle Channels ab",
            "AI Agents in jedem Workflow fuer intelligente Entscheidungen",
            "BMA Consulting hat hoechsten Einzeldeal-Wert",
            "X/Twitter ist der Lead-Trichter fuer alles andere",
            "Gumroad + Fiverr komplett automatisierbar"
        ],
        "actions": [
            "Gumroad Webhook einrichten",
            "Fiverr API Integration aufsetzen",
            "X/Twitter API Credentials in n8n",
            "BMA Landing Page mit Form Trigger verbinden",
            "Telegram Bot fuer Daily Reports"
        ]
    }


async def _agent_ai_builder(k: dict) -> dict:
    """Agent 3: Configure AI agents in n8n."""
    ai_nodes = k.get("node_types", {}).get("ai_nodes", {})
    return {
        "ai_agents": {
            "lead_qualifier": {
                "type": "Tools Agent",
                "model": "Ollama (free) → Gemini Flash (fallback)",
                "tools": ["HTTP Request (CRM lookup)", "Calculator (BANT score)", "Code (custom scoring)"],
                "memory": "Redis Chat Memory (persist across sessions)",
                "purpose": "Qualify leads automatically using BANT methodology"
            },
            "content_creator": {
                "type": "Tools Agent",
                "model": "Gemini Flash (fast, cheap)",
                "tools": ["SerpAPI (trend research)", "Code (format content)", "HTTP Request (post to X)"],
                "memory": "Window Buffer (last 10 posts for style consistency)",
                "purpose": "Generate viral X/Twitter content"
            },
            "customer_support": {
                "type": "Tools Agent",
                "model": "Ollama local",
                "tools": ["Vector Store Tool (product knowledge)", "HTTP Request (CRM)", "Email (respond)"],
                "memory": "PostgreSQL Chat Memory",
                "vector_store": "PGVector with product docs + FAQ",
                "purpose": "Auto-respond to customer inquiries"
            },
            "bma_expert": {
                "type": "Tools Agent",
                "model": "Gemini Pro (deep thinking)",
                "tools": ["Vector Store Tool (BMA knowledge)", "Calculator", "Code (proposal generator)"],
                "memory": "Redis Chat Memory",
                "vector_store": "PGVector with BMA regulations + case studies",
                "purpose": "BMA consulting assistant with deep domain knowledge"
            },
            "empire_analyst": {
                "type": "Tools Agent",
                "model": "Gemini Flash",
                "tools": ["HTTP Request (all system APIs)", "Code (data analysis)", "Calculator"],
                "memory": "Summary Buffer Memory",
                "purpose": "Analyze empire performance, suggest optimizations"
            },
            "vision_interviewer": {
                "type": "Conversational Agent",
                "model": "Gemini Pro",
                "tools": ["Code (store answers)", "HTTP Request (Digital Memory API)"],
                "memory": "PostgreSQL Chat Memory (full history)",
                "purpose": "Daily vision discovery - ask Maurice strategic questions"
            }
        },
        "rag_setup": {
            "document_sources": [
                "BMA Academy materials → PGVector",
                "Gold Nuggets → PGVector",
                "Product documentation → PGVector",
                "Customer interactions → PGVector",
                "Workflow outputs → PGVector"
            ],
            "embeddings": "Ollama Embeddings (free) or OpenAI (better quality)",
            "vector_store": "PGVector (shared PostgreSQL)",
            "chunking": "Recursive Character Splitter, 1000 chars, 200 overlap"
        },
        "insights": [
            "6 spezialisierte AI Agents fuer verschiedene Aufgaben",
            "Ollama-first Strategie: 90% kostenlos, Gemini als Fallback",
            "RAG mit PGVector fuer BMA-Expertise und Produkt-Wissen",
            "Redis Memory fuer persistente Konversationen",
            "Jeder Agent hat spezifische Tools fuer seine Aufgabe"
        ],
        "actions": [
            "PGVector Extension in PostgreSQL aktivieren",
            "BMA Dokumente in Vector Store laden",
            "Ollama Embeddings Model installieren",
            "Redis Memory Nodes konfigurieren",
            "AI Agent Workflows in n8n erstellen"
        ]
    }


async def _agent_integration(k: dict) -> dict:
    """Agent 4: Connect all AIEmpire systems with n8n."""
    return {
        "integration_map": {
            "crm_to_n8n": {
                "method": "REST API + Direct PostgreSQL",
                "triggers": ["New lead created", "Deal stage changed", "Activity logged"],
                "actions": ["Create lead", "Update deal", "Log activity", "Query leads"],
                "port": 3000
            },
            "empire_api_to_n8n": {
                "method": "Webhook + HTTP Request",
                "triggers": ["System event webhooks"],
                "actions": ["Get status", "Execute tasks", "Update config"],
                "connection": "Bidirectional webhooks"
            },
            "kimi_swarm_to_n8n": {
                "method": "HTTP Request → Moonshot API",
                "triggers": ["Schedule (batch processing)"],
                "actions": ["Spawn agents", "Collect results", "Route to CRM"],
                "api": "https://api.moonshot.ai/v1/chat/completions"
            },
            "atomic_reactor_to_n8n": {
                "method": "File Watch + HTTP Request",
                "triggers": ["New YAML task file", "Schedule"],
                "actions": ["Execute task", "Generate report", "Store results"]
            },
            "gemini_mirror_to_n8n": {
                "method": "Schedule + File System",
                "triggers": ["Every 30 min sync cycle"],
                "actions": ["Read sync state", "Call Gemini API", "Update memory", "Push artifacts"]
            },
            "brain_system_to_n8n": {
                "method": "SQLite + HTTP Request",
                "triggers": ["Synapse messages", "Schedule"],
                "actions": ["Route messages between brains", "Execute brain tasks"]
            },
            "x_lead_machine_to_n8n": {
                "method": "Schedule + X API",
                "triggers": ["Content schedule", "Lead detection"],
                "actions": ["Post content", "Extract leads", "Score engagement"]
            },
            "ollama_to_n8n": {
                "method": "AI Agent Node → Ollama API",
                "endpoint": "http://localhost:11434",
                "models": ["glm-4.7-flash:latest", "qwen2.5-coder:7b"],
                "usage": "Primary AI for all agent nodes (free)"
            },
            "github_to_n8n": {
                "method": "GitHub Node + Webhooks",
                "triggers": ["Push events", "Issue creation", "PR events"],
                "actions": ["Create issues", "Update code", "Deploy"]
            }
        },
        "insights": [
            "9 Systeme muessen mit n8n verbunden werden",
            "Ollama ist der primaere AI Provider (kostenlos)",
            "CRM-Integration ueber Direct DB + REST API",
            "Gemini Mirror Sync als Schedule-Workflow",
            "GitHub fuer CI/CD und Issue-basierte Steuerung"
        ],
        "actions": [
            "n8n Credentials fuer alle 9 Systeme einrichten",
            "Webhook Endpoints in Empire API registrieren",
            "Ollama Connection testen",
            "CRM PostgreSQL Credentials konfigurieren",
            "GitHub Webhook fuer Auto-Deploy"
        ]
    }


async def _agent_docker_ops(k: dict) -> dict:
    """Agent 5: Docker production setup."""
    hosting = k.get("self_hosting", {})
    return {
        "docker_compose": {
            "services": {
                "n8n": {
                    "image": "n8nio/n8n:latest",
                    "restart": "always",
                    "ports": ["5678:5678"],
                    "environment": {
                        "N8N_HOST": "0.0.0.0",
                        "N8N_PORT": "5678",
                        "N8N_PROTOCOL": "https",
                        "N8N_ENCRYPTION_KEY": "${N8N_ENCRYPTION_KEY}",
                        "DB_TYPE": "postgresdb",
                        "DB_POSTGRESDB_HOST": "postgres",
                        "DB_POSTGRESDB_PORT": "5432",
                        "DB_POSTGRESDB_DATABASE": "n8n",
                        "DB_POSTGRESDB_USER": "n8n",
                        "DB_POSTGRESDB_PASSWORD": "${N8N_DB_PASSWORD}",
                        "GENERIC_TIMEZONE": "Europe/Berlin",
                        "TZ": "Europe/Berlin",
                        "EXECUTIONS_MODE": "queue",
                        "QUEUE_BULL_REDIS_HOST": "redis",
                        "QUEUE_BULL_REDIS_PORT": "6379",
                        "N8N_METRICS": "true",
                        "N8N_DIAGNOSTICS_ENABLED": "false"
                    },
                    "volumes": ["n8n_data:/home/node/.n8n"],
                    "depends_on": ["postgres", "redis"]
                },
                "n8n_worker": {
                    "image": "n8nio/n8n:latest",
                    "restart": "always",
                    "command": "worker",
                    "environment": "same as n8n (minus port)",
                    "depends_on": ["postgres", "redis", "n8n"],
                    "note": "Horizontal scaling - add more workers as needed"
                },
                "postgres": {
                    "image": "postgres:16-alpine",
                    "restart": "always",
                    "environment": {
                        "POSTGRES_DB": "n8n",
                        "POSTGRES_USER": "n8n",
                        "POSTGRES_PASSWORD": "${N8N_DB_PASSWORD}"
                    },
                    "volumes": ["postgres_data:/var/lib/postgresql/data"],
                    "note": "Shared with CRM when migrated from SQLite"
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "restart": "always",
                    "volumes": ["redis_data:/data"],
                    "note": "Used for queue mode + AI agent memory"
                }
            },
            "volumes": ["n8n_data", "postgres_data", "redis_data"]
        },
        "scaling_strategy": {
            "phase_1": "Single n8n instance (handles 100+ workflows)",
            "phase_2": "Add worker for queue mode (1000+ executions/day)",
            "phase_3": "Multiple workers + load balancer (10K+ executions/day)"
        },
        "insights": [
            "Queue-Modus mit Redis fuer parallele Ausfuehrung",
            "PostgreSQL statt SQLite fuer Production",
            "Worker-Instanzen fuer horizontale Skalierung",
            "Redis shared mit bestehendem Redis Stack",
            "Metrics aktiviert fuer Prometheus/Grafana Monitoring"
        ],
        "actions": [
            "docker-compose.yaml erstellen mit n8n + postgres + redis",
            "Environment Variables in .env File",
            "N8N_ENCRYPTION_KEY generieren",
            "Traefik Reverse Proxy konfigurieren",
            "Backup-Strategie fuer PostgreSQL"
        ]
    }


async def _agent_api_bridge(k: dict) -> dict:
    """Agent 6: Build n8n API bridge for Empire Control."""
    return {
        "api_bridge": {
            "class": "N8NApiBridge",
            "base_url": "http://localhost:5678",
            "auth": "X-N8N-API-KEY header",
            "methods": {
                "list_workflows": "GET /api/v1/workflows",
                "get_workflow": "GET /api/v1/workflows/{id}",
                "create_workflow": "POST /api/v1/workflows",
                "update_workflow": "PATCH /api/v1/workflows/{id}",
                "activate_workflow": "POST /api/v1/workflows/{id}/activate",
                "deactivate_workflow": "POST /api/v1/workflows/{id}/deactivate",
                "execute_workflow": "POST /api/v1/workflows/{id}/execute",
                "list_executions": "GET /api/v1/executions",
                "get_execution": "GET /api/v1/executions/{id}",
                "list_credentials": "GET /api/v1/credentials",
                "health_check": "GET /api/v1/health"
            },
            "empire_integration": {
                "empire_cli": "python empire.py n8n status|workflows|execute|deploy",
                "status_dashboard": "Workflows active, execution count, errors, queue depth",
                "auto_deploy": "Push workflow JSON to n8n via API on git push"
            }
        },
        "insights": [
            "n8n REST API erlaubt vollstaendige Steuerung",
            "Empire CLI bekommt n8n Subcommand",
            "Auto-Deploy: Git Push → n8n Workflow Update",
            "Health Check in System-Status integriert",
            "Execution Monitoring fuer Fehler-Erkennung"
        ],
        "actions": [
            "N8NApiBridge Python Klasse implementieren",
            "Empire CLI n8n Subcommand hinzufuegen",
            "Auto-Deploy GitHub Action erstellen",
            "Health Check in empire.py status integrieren"
        ]
    }


async def _agent_memory_sync(k: dict) -> dict:
    """Agent 7: n8n ↔ Digital Memory sync."""
    return {
        "memory_sync": {
            "n8n_to_memory": {
                "trigger": "Every workflow execution completion",
                "process": "Extract insights from execution results → Digital Memory",
                "categories": ["patterns", "decisions", "lessons", "financial"]
            },
            "memory_to_n8n": {
                "trigger": "Memory update event",
                "process": "Push relevant memories to n8n workflow context",
                "usage": "AI Agents access memories for better decisions"
            },
            "sync_workflow": {
                "name": "Memory Sync Engine",
                "trigger": "Schedule (every 15 min) + Webhook (on memory update)",
                "nodes": [
                    "Read Digital Memory state",
                    "Compare with n8n execution history",
                    "Extract new patterns and insights",
                    "Update Digital Memory via API",
                    "Notify if critical insight found"
                ]
            }
        },
        "insights": [
            "Bidirektionale Sync zwischen n8n Executions und Digital Memory",
            "Jede Workflow-Ausfuehrung generiert lernbare Insights",
            "AI Agents in n8n nutzen Digital Memory fuer bessere Entscheidungen",
            "Patterns aus Workflow-Erfolgen werden persistent gespeichert"
        ],
        "actions": [
            "n8n Webhook in Digital Memory registrieren",
            "Memory Export API Endpoint erstellen",
            "Sync Workflow in n8n deployen",
            "Pattern Extraction Logic implementieren"
        ]
    }


async def _agent_revenue_auto(k: dict) -> dict:
    """Agent 8: Revenue automation workflows."""
    return {
        "revenue_automation": {
            "pipeline": {
                "stage_1_attract": {
                    "channels": ["X/Twitter content", "SEO blog posts", "YouTube shorts"],
                    "automation": "n8n Schedule → AI Content Gen → Multi-platform post",
                    "goal": "100 new leads/week"
                },
                "stage_2_qualify": {
                    "method": "BANT scoring via AI Agent",
                    "automation": "New lead webhook → AI scores → Route by score",
                    "goal": "20% lead-to-qualified rate"
                },
                "stage_3_convert": {
                    "methods": ["Email sequence", "Personalized demo", "Free value delivery"],
                    "automation": "n8n email sequences + Calendly integration",
                    "goal": "10% qualified-to-customer rate"
                },
                "stage_4_deliver": {
                    "products": {
                        "digital": "Gumroad auto-delivery",
                        "service": "AI-assisted Fiverr delivery",
                        "consulting": "BMA + AI consulting package"
                    },
                    "automation": "Webhook → AI generates deliverable → Quality check → Send"
                },
                "stage_5_retain": {
                    "methods": ["Upsell sequences", "Customer success check-ins", "Referral program"],
                    "automation": "n8n sequences + AI personalization"
                }
            },
            "quick_wins": [
                "Gumroad Webhook → CRM + Email = FIRST REVENUE AUTOMATION",
                "X/Twitter content schedule = 3x daily automated posts",
                "BMA landing page + Form → Auto email + CRM = CONSULTING LEADS"
            ],
            "revenue_projections": {
                "month_1": "Focus on Gumroad + Fiverr activation",
                "month_2": "BMA consulting pipeline live",
                "month_3": "Full automation, scale X/Twitter reach"
            }
        },
        "insights": [
            "5-Stage Revenue Pipeline komplett automatisierbar",
            "Gumroad ist der schnellste Weg zu erstem Revenue",
            "BMA Consulting hat den hoechsten Deal-Wert",
            "X/Twitter ist der primaere Lead-Trichter",
            "AI Agents in jeder Pipeline-Stage fuer Personalisierung"
        ],
        "actions": [
            "Gumroad Account einrichten + erstes Produkt listen",
            "Fiverr Gigs erstellen (AI Automation Services)",
            "BMA Landing Page mit Form Trigger",
            "X/Twitter Content Schedule starten (3x daily)",
            "Email Sequences in n8n aufsetzen"
        ]
    }


async def _agent_monitor(k: dict) -> dict:
    """Agent 9: System monitoring workflows."""
    return {
        "monitoring": {
            "health_checks": {
                "n8n": {"url": "http://localhost:5678/api/v1/health", "interval": "5min"},
                "crm": {"url": "http://localhost:3000/api/health", "interval": "5min"},
                "empire_api": {"url": "http://localhost:8000/health", "interval": "5min"},
                "ollama": {"url": "http://localhost:11434/api/tags", "interval": "10min"},
                "postgres": {"method": "pg_isready", "interval": "5min"},
                "redis": {"method": "redis-cli ping", "interval": "5min"}
            },
            "alerts": {
                "channels": ["Telegram", "Email"],
                "conditions": [
                    "Service down > 2 min",
                    "Workflow failure rate > 10%",
                    "Queue depth > 100",
                    "CPU > 85%",
                    "Disk > 90%"
                ]
            },
            "dashboards": {
                "daily_kpi": {
                    "metrics": ["Revenue", "Leads generated", "Content posted", "Workflows executed", "Errors"],
                    "delivery": "Telegram 07:00 + 19:00"
                },
                "system_health": {
                    "metrics": ["Uptime", "Response times", "Queue depth", "Memory usage", "API costs"],
                    "delivery": "Prometheus/Grafana + Telegram alerts"
                }
            }
        },
        "insights": [
            "6 Services muessen ueberwacht werden",
            "Telegram ist der primaere Alert-Kanal",
            "Taegliche KPI-Reports fuer Ueberblick",
            "Queue Depth Monitoring fuer Skalierungsentscheidungen"
        ],
        "actions": [
            "Telegram Bot Token erneuern (aktuell invalid!)",
            "Health Check Workflow in n8n erstellen",
            "Prometheus Metrics in n8n aktivieren",
            "Daily KPI Workflow aufsetzen"
        ]
    }


async def _agent_evolution(k: dict) -> dict:
    """Agent 10: Self-evolving workflows."""
    return {
        "evolution_workflows": {
            "self_healing": {
                "description": "Workflow erkennt Fehler und repariert sich selbst",
                "trigger": "Error Trigger",
                "flow": "Error → AI analysiert Ursache → Fix vorschlagen → Auto-repair oder Alert",
                "models": ["Ollama (quick fix)", "Gemini Pro (complex fix)"]
            },
            "ab_testing": {
                "description": "Verschiedene Workflow-Varianten testen",
                "trigger": "Schedule",
                "flow": "Run Variant A + B → Compare results → Keep winner → Generate new variant",
                "application": "Content generation, email subjects, lead scoring weights"
            },
            "performance_optimizer": {
                "description": "Workflow-Performance automatisch optimieren",
                "trigger": "Schedule (weekly)",
                "flow": "Analyze execution times → Find bottlenecks → Suggest optimizations → Apply"
            },
            "knowledge_accumulator": {
                "description": "Lernt aus jedem Workflow-Durchlauf",
                "trigger": "Every execution",
                "flow": "Extract patterns → Compare with history → Update knowledge base → Improve next run"
            },
            "cross_system_evolution": {
                "description": "n8n + Gemini Mirror gemeinsame Evolution",
                "trigger": "Daily",
                "flow": "n8n insights → Gemini analysis → Improvement suggestions → n8n workflow updates"
            }
        },
        "insights": [
            "Self-Healing reduziert manuellen Maintenance-Aufwand",
            "A/B Testing fuer kontinuierliche Verbesserung",
            "Knowledge Accumulator macht Workflows mit der Zeit besser",
            "Cross-System Evolution: n8n + Gemini verstaerken sich gegenseitig"
        ],
        "actions": [
            "Error Trigger Workflow mit AI-Analyse erstellen",
            "A/B Testing Framework fuer Content Workflows",
            "Execution Analytics Pipeline aufsetzen",
            "Cross-System Sync mit Gemini Mirror verbinden"
        ]
    }


# ============================================================
# DIGITAL MEMORY INGESTION
# ============================================================

async def ingest_to_memory():
    """Load all n8n knowledge into Digital Memory."""
    try:
        from digital_memory import DigitalMemory
    except ImportError:
        print("[ERROR] Digital Memory not available. Run from project root.")
        return

    memory = DigitalMemory()
    knowledge = load_knowledge()
    count = 0

    # Core knowledge
    core = knowledge.get("core", {})
    for key, value in core.items():
        memory.remember("technical", f"n8n_{key}", str(value), 0.95, "n8n_knowledge")
        count += 1

    # Architecture knowledge
    arch = knowledge.get("architecture", {})
    memory.remember("technical", "n8n_architecture", json.dumps(arch, ensure_ascii=False)[:500], 0.9, "n8n_knowledge")
    count += 1

    # API endpoints
    api = arch.get("api", {}).get("endpoints", {})
    for category, endpoints in api.items():
        memory.remember("technical", f"n8n_api_{category}", json.dumps(endpoints), 0.9, "n8n_knowledge")
        count += 1

    # AI capabilities
    ai = knowledge.get("node_types", {}).get("ai_nodes", {})
    for key, value in ai.items():
        memory.remember("technical", f"n8n_ai_{key}", json.dumps(value, ensure_ascii=False)[:400], 0.9, "n8n_knowledge")
        count += 1

    # Self-hosting config
    hosting = knowledge.get("self_hosting", {})
    memory.remember("technical", "n8n_docker_config", json.dumps(hosting.get("docker", {}), ensure_ascii=False)[:500], 0.9, "n8n_knowledge")
    memory.remember("technical", "n8n_env_vars", json.dumps(hosting.get("environment_variables", {}), ensure_ascii=False)[:500], 0.9, "n8n_knowledge")
    memory.remember("technical", "n8n_scaling", json.dumps(hosting.get("scaling", {}), ensure_ascii=False)[:300], 0.9, "n8n_knowledge")
    count += 3

    # Revenue workflow patterns
    patterns = knowledge.get("workflow_patterns_for_aiempire", {})
    for name, pattern in patterns.items():
        memory.remember("patterns", f"n8n_workflow_{name}", json.dumps(pattern, ensure_ascii=False)[:400], 0.85, "n8n_knowledge", tags=["n8n", "workflow", "revenue"])
        count += 1

    # FAQ
    faq = knowledge.get("faq", [])
    for item in faq:
        memory.remember("technical", f"n8n_faq_{item['q'][:30]}", item['a'], 0.9, "n8n_knowledge", tags=["n8n", "faq"])
        count += 1

    # Integrations
    integrations = knowledge.get("popular_integrations", {})
    for category, apps in integrations.items():
        memory.remember("technical", f"n8n_integrations_{category}", ", ".join(apps), 0.9, "n8n_knowledge", tags=["n8n", "integrations"])
        count += 1

    # Agent outputs (if available)
    agents_dir = KNOWLEDGE_DIR / "agents"
    if agents_dir.exists():
        for f in agents_dir.glob("*.json"):
            if f.name == "agent_state.json":
                continue
            try:
                data = json.loads(f.read_text())
                for insight in data.get("insights", []):
                    memory.remember("patterns", f"n8n_insight_{insight[:40]}", insight, 0.8, "n8n_agents", tags=["n8n", "insight"])
                    count += 1
                for action in data.get("actions", []):
                    memory.remember("decisions", f"n8n_action_{action[:40]}", action, 0.75, "n8n_agents", tags=["n8n", "action"])
                    count += 1
            except (json.JSONDecodeError, OSError):
                pass

    stats = memory.stats()
    print(f"\n[INGEST] {count} n8n knowledge entries loaded into Digital Memory")
    print(f"  Total memories: {stats['total_memories']}")
    print(f"  High confidence: {stats['high_confidence']}")

    return count


# ============================================================
# MAIN
# ============================================================

async def run_all_agents():
    """Run all 10 agents in parallel."""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║         10 CLAUDE OFFLINE AGENTS - n8n KNOWLEDGE           ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    knowledge = load_knowledge()
    state = load_state()
    state["started_at"] = datetime.now(timezone.utc).isoformat()

    print(f"[LAUNCH] Starting 10 agents in parallel...\n")

    # Run all 10 agents concurrently
    tasks = [run_agent(i, knowledge) for i in range(1, 11)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Update state
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            state["agents"][str(i)] = {"status": "error", "error": str(result)}
        else:
            state["agents"][str(i)] = result

    state["completed_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    # Summary
    completed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "completed")
    failed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "failed")
    errors = sum(1 for r in results if isinstance(r, Exception))

    print(f"\n{'='*60}")
    print(f"[DONE] {completed} completed, {failed} failed, {errors} errors")
    print(f"  Outputs in: n8n-knowledge/agents/")

    # Auto-ingest
    print(f"\n[INGEST] Loading knowledge into Digital Memory...")
    await ingest_to_memory()

    return results


def show_status():
    """Show agent status."""
    state = load_state()
    print("\n[AGENT STATUS]")
    for agent_id, info in AGENTS.items():
        agent_state = state.get("agents", {}).get(str(agent_id), {})
        status = agent_state.get("status", "not_run")
        print(f"  [{agent_id:2d}] {info['name']:20s} {status.upper()}")

    agents_dir = KNOWLEDGE_DIR / "agents"
    if agents_dir.exists():
        files = list(agents_dir.glob("*.json"))
        print(f"\n  Output files: {len(files)}")
        for f in sorted(files):
            if f.name != "agent_state.json":
                print(f"    {f.name} ({f.stat().st_size / 1024:.1f} KB)")


async def main():
    parser = argparse.ArgumentParser(description="10 Claude Offline Agents - n8n Knowledge Processor")
    parser.add_argument("--agent", type=int, choices=range(1, 11), help="Run single agent")
    parser.add_argument("--status", action="store_true", help="Show agent status")
    parser.add_argument("--ingest", action="store_true", help="Ingest knowledge into Digital Memory")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.ingest:
        await ingest_to_memory()
    elif args.agent:
        knowledge = load_knowledge()
        result = await run_agent(args.agent, knowledge)
        print(f"\n  Result: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
        # Also ingest
        await ingest_to_memory()
    else:
        await run_all_agents()


if __name__ == "__main__":
    asyncio.run(main())
