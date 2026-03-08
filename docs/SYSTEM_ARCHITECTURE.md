# SYSTEM ARCHITECTURE - Maurice's AI Empire
# Stand: 2026-02-08

## VISUAL ARCHITECTURE (Mermaid Diagram)

```mermaid
graph TB
    subgraph "MAURICE (Human)"
        M[Maurice<br/>Elektrotechnikmeister<br/>16J BMA-Expertise]
    end

    subgraph "CONTROL LAYER"
        CC[Claude Code<br/>Strategic AI<br/>Opus/Sonnet]
        GH[GitHub<br/>mauricepfeifer-ctrl/AIEmpire-Core<br/>Code + Gold Nuggets + Docs]
        CP[GitHub Copilot<br/>ChatGPT Mini 5<br/>Execution Agent]
    end

    subgraph "OPENCLAW (Personal AI Agent)"
        OC[OpenClaw Gateway<br/>Port 18789<br/>v2026.2.2-3]
        CRON[9 Cron Jobs<br/>08:00-19:00 Daily]
        SKILLS[Skills Engine<br/>ClawHub Marketplace]
    end

    subgraph "AI MODELS"
        OL[Ollama<br/>Port 11434<br/>qwen2.5-coder:7b<br/>KOSTENLOS]
        KI[Kimi K2.5<br/>api.moonshot.ai<br/>256K Context<br/>$7.72 Budget]
    end

    subgraph "DATA LAYER"
        RD[Redis<br/>Port 6379<br/>Queue + Cache]
        PG[PostgreSQL<br/>Port 5432<br/>Persistent Data]
    end

    subgraph "ATOMIC REACTOR"
        AR[FastAPI Server<br/>Port 8888<br/>Task Orchestration]
        TQ[Task Queues<br/>kimi/claude/ollama/chatgpt]
        SW[Swarm Engine<br/>50.000 Max Agents]
    end

    subgraph "REVENUE SYSTEMS"
        GM[Gumroad<br/>Digital Products<br/>EUR 27-149]
        FV[Fiverr/Upwork<br/>AI Services<br/>EUR 30-5000]
        XL[X/Twitter<br/>Content + Leads]
        TG[Telegram<br/>Community + Bot]
    end

    subgraph "CONTENT PIPELINE"
        RS[Research Agent<br/>Trends + Keywords]
        CA[Content Agent<br/>Posts + Articles + Videos]
        SA[Sales Agent<br/>Leads + Outreach]
        EA[Engagement Agent<br/>Replies + DMs]
        AN[Analytics Agent<br/>KPIs + Revenue]
    end

    M -->|Steuert| CC
    CC -->|Push/Pull| GH
    GH -->|Liest/Ausfuehrt| CP
    CP -->|Updates| GH

    M -->|Messaging| OC
    OC -->|Routes to| OL
    OC -->|Fallback| KI
    OC -->|Schedules| CRON

    CRON --> RS
    CRON --> CA
    CRON --> SA
    CRON --> EA
    CRON --> AN

    AR --> TQ
    TQ --> OL
    TQ --> KI
    AR --> SW

    RS -->|Trends| CA
    CA -->|Content| XL
    CA -->|Products| GM
    SA -->|Leads| FV
    EA -->|Community| TG

    OC --> RD
    AR --> RD
    AR --> PG
```

## COMPONENT STATUS MAP

```
╔══════════════════════════════════════════════════════════════╗
║                  MAURICE'S AI EMPIRE                        ║
║                  Status: 2026-02-08                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌─────────────────┐  ┌─────────────────┐                   ║
║  │ CLAUDE CODE     │  │ GITHUB          │                   ║
║  │ ✅ Active       │→→│ ✅ Connected    │                   ║
║  │ Opus/Sonnet     │  │ AIEmpire-Core   │                   ║
║  └────────┬────────┘  └────────┬────────┘                   ║
║           │                     │                            ║
║           ▼                     ▼                            ║
║  ┌─────────────────┐  ┌─────────────────┐                   ║
║  │ OPENCLAW        │  │ COPILOT/GPT     │                   ║
║  │ ✅ Running      │  │ ✅ Connected    │                   ║
║  │ Port 18789      │  │ ChatGPT Mini 5  │                   ║
║  │ 9 Cron Jobs     │  │ via GitHub      │                   ║
║  └────────┬────────┘  └─────────────────┘                   ║
║           │                                                  ║
║           ▼                                                  ║
║  ┌─────────────────┐  ┌─────────────────┐                   ║
║  │ OLLAMA          │  │ KIMI K2.5       │                   ║
║  │ ⏳ Loading      │  │ ✅ Active       │                   ║
║  │ Port 11434      │  │ $7.72 Budget    │                   ║
║  │ qwen2.5-coder   │  │ 256K Context    │                   ║
║  └────────┬────────┘  └────────┬────────┘                   ║
║           │                     │                            ║
║           ▼                     ▼                            ║
║  ┌─────────────────┐  ┌─────────────────┐                   ║
║  │ REDIS           │  │ POSTGRESQL      │                   ║
║  │ ⚠️ Restart      │  │ ⚠️ Restart     │                   ║
║  │ Port 6379       │  │ Port 5432       │                   ║
║  └─────────────────┘  └─────────────────┘                   ║
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │ ATOMIC REACTOR                                       │   ║
║  │ ⚠️ Not Running (Port 8888)                          │   ║
║  │ 5 Tasks defined, 50K max agents, Swarm ready        │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │ REVENUE CHANNELS                                     │   ║
║  │ Gumroad: ✅ (1 product)  Fiverr: ❌ (0 gigs)       │   ║
║  │ X/Twitter: ⚠️ (posts ready)  Telegram: ❌ (no bot) │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║  REVENUE: EUR 0  │  TARGET: EUR 50-100 overnight            ║
╚══════════════════════════════════════════════════════════════╝
```

## DATA FLOW

```
INPUT                    PROCESSING              OUTPUT
─────                    ──────────              ──────
Trends (X/YT/TT)  ───→  Research Agent    ───→  Trend Report
                         │
Trend Report       ───→  Content Agent    ───→  Posts/Scripts/Articles
                         │
Content Posted     ───→  Engagement Agent ───→  Replies/DMs
                         │
Leads Generated    ───→  Sales Agent      ───→  Outreach/Follow-up
                         │
All Data           ───→  Analytics Agent  ───→  KPI Dashboard
                         │
Revenue Data       ───→  Finance Agent    ───→  Weekly Review
```

## MODEL ROUTING

```
Task Type        → Model         → Cost      → Speed
─────────        ─ ─────         ─ ────      ─ ─────
Simple/Bulk      → Ollama        → FREE      → 100-500ms
Classification   → Ollama        → FREE      → 50-200ms
Research         → Kimi K2.5     → $0.0005   → 1-3s
Decomposition    → Kimi K2.5     → $0.0005   → 1-3s
Content Writing  → Kimi K2.5     → $0.001    → 2-5s
Coding           → Claude        → $$        → 5-10s
Strategy         → Claude Opus   → $$$       → 10-30s
Creative         → ChatGPT       → $$        → 3-8s

ROUTING RULE:
95% Ollama (FREE) → 4% Kimi ($0.001) → 0.9% Haiku → 0.1% Opus
```
