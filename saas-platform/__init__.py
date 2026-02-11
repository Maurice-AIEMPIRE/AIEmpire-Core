"""
AIEmpire SaaS Platform
=======================
Cloud-native AI Business Automation Platform as a Service.

Jeder Kunde bekommt seine eigene Empire-Instanz:
- Eigene AI Agents (Workflow, Cowork, Gemini Mirror)
- Eigene Datenbank + Redis
- Eigene API Keys + Konfiguration
- Isoliert in eigenem Namespace/Container

Architektur:
  ┌─────────────────────────────────────────────┐
  │           SAAS PLATFORM (Control Plane)      │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
  │  │ API GW   │  │ Billing  │  │ Admin    │  │
  │  │ (Auth+   │  │ (Stripe) │  │ Dashboard│  │
  │  │  Route)  │  │          │  │          │  │
  │  └────┬─────┘  └──────────┘  └──────────┘  │
  └───────┼─────────────────────────────────────┘
          │
  ┌───────┼─────────────────────────────────────┐
  │       │     TENANT DATA PLANE               │
  │  ┌────▼─────┐  ┌──────────┐  ┌──────────┐  │
  │  │ Tenant A │  │ Tenant B │  │ Tenant C │  │
  │  │ Empire   │  │ Empire   │  │ Empire   │  │
  │  │ Instance │  │ Instance │  │ Instance │  │
  │  └──────────┘  └──────────┘  └──────────┘  │
  └─────────────────────────────────────────────┘

Pricing:
  Starter:     49 EUR/mo  (1 Agent Team, 5K API calls)
  Pro:        149 EUR/mo  (5 Agent Teams, 50K API calls, Gemini Mirror)
  Enterprise: 499 EUR/mo  (Unlimited, Custom Agents, Priority Support)
"""

__version__ = "0.1.0"
__product__ = "AIEmpire Cloud"
