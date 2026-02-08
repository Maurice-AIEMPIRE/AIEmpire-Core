# 🏗️ Infrastruktur

Docker, Compose, Caddy-Konfigurationen und Deployment-Skripte.

## Struktur

```
infra/
├── docker-compose.yaml    # Haupt-Compose für alle Services
├── caddy/                 # Reverse Proxy Konfiguration
├── scripts/               # Deployment & Maintenance Skripte
└── README.md
```

## Services

| Service    | Port  | Beschreibung                    |
|------------|-------|---------------------------------|
| Ollama     | 11434 | Lokales LLM                     |
| ChromaDB   | 8100  | Vektor-Datenbank                |
| Redis      | 6379  | Cache & Task Queue              |
| CRM        | 3500  | Lead Management                 |

## Schnellstart

```bash
docker compose up -d
```

## Referenzen

Bestehende Compose-Dateien befinden sich auch in:
- `atomic-reactor/docker-compose.yaml` - Task Orchestrator
- `systems/docker-compose.yaml` - Kern-Infrastruktur
- `openclaw-config/docker-compose.yaml` - OpenClaw Setup
