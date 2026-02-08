# n8n Workflows - AI Empire

## System
- n8n v2.6.4: http://localhost:5678
- LaunchAgent: com.ai-empire.n8n (Keepalive alle 60s)
- Logs: ~/.openclaw/workspace/ai-empire/00_SYSTEM/logs/n8n.log

## Workflows

| # | Name | Trigger | Verbindungen |
|---|------|---------|--------------|
| 01 | Content Engine | 4x daily | Ollama → X/Twitter Posts |
| 02 | Ollama Brain | Webhook | Zentrale AI Node |
| 03 | Kimi Router | Webhook | Kimi K2.5 (temp=1.0!) |
| 04 | GitHub Monitor | 30 min | Issues, PRs, Stars |
| 05 | System Health | 5 min | Ollama, OpenClaw, n8n, Redis |
| 06 | Lead Generator | daily 09:00 | BMA, AI Consulting, Automation |

## Import
```bash
# Via API (nach Setup):
export N8N_API_KEY="dein-api-key"
for f in n8n-workflows/0*.json; do
  curl -X POST http://localhost:5678/api/v1/workflows \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$f"
done
```

## Oder manuell:
1. http://localhost:5678 oeffnen
2. Workflows → Import from File
3. JSON auswaehlen

## Services
- Ollama: localhost:11434 (qwen2.5-coder:7b)
- Kimi: api.moonshot.ai/v1 (MOONSHOT_API_KEY, temp=1.0!)
- OpenClaw: localhost:8080
- Redis: localhost:6379
- PostgreSQL: localhost:5432
- GitHub: mauricepfeifer-ctrl/AIEmpire-Core
