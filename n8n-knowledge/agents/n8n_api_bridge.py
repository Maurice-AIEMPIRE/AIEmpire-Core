{
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