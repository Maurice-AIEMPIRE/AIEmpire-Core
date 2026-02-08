#!/usr/bin/env python3
"""
n8n <-> AI Empire Connector
Bridges n8n workflows with OpenClaw, Brain System, and all services.

Usage:
    python3 n8n_connector.py --status       # Check all services
    python3 n8n_connector.py --trigger WF   # Trigger workflow by name
    python3 n8n_connector.py --webhooks     # List all webhook URLs
    python3 n8n_connector.py --import-all   # Import all workflows
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Config
N8N_URL = "http://localhost:5678"
OLLAMA_URL = "http://localhost:11434"
OPENCLAW_URL = "http://localhost:8080"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

API_KEY = os.environ.get("N8N_API_KEY", "")
WORKFLOW_DIR = Path(__file__).parent
LOG_DIR = Path.home() / ".openclaw/workspace/ai-empire/00_SYSTEM/logs"


def check_service(name, url, path="/"):
    """Check if a service is running."""
    try:
        req = urllib.request.urlopen(f"{url}{path}", timeout=5)
        return {"name": name, "status": "UP", "code": req.getcode()}
    except Exception as e:
        return {"name": name, "status": "DOWN", "error": str(e)}


def check_redis():
    """Check Redis via redis-cli."""
    try:
        result = subprocess.run(
            ["redis-cli", "-h", REDIS_HOST, "-p", str(REDIS_PORT), "ping"],
            capture_output=True, text=True, timeout=5
        )
        if "PONG" in result.stdout:
            return {"name": "Redis", "status": "UP", "response": "PONG"}
        return {"name": "Redis", "status": "DOWN", "error": result.stderr}
    except Exception as e:
        return {"name": "Redis", "status": "DOWN", "error": str(e)}


def system_status():
    """Full system health check."""
    services = [
        check_service("n8n", N8N_URL, "/healthz"),
        check_service("Ollama", OLLAMA_URL, "/api/tags"),
        check_service("OpenClaw", OPENCLAW_URL, "/health"),
        check_redis(),
    ]

    print("=" * 50)
    print(f"AI EMPIRE SYSTEM STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    all_up = True
    for svc in services:
        icon = "✅" if svc["status"] == "UP" else "❌"
        print(f"  {icon} {svc['name']}: {svc['status']}")
        if svc["status"] != "UP":
            all_up = False
            print(f"     Error: {svc.get('error', 'unknown')}")

    print("=" * 50)
    print(f"Overall: {'ALL SYSTEMS GO' if all_up else 'DEGRADED'}")
    return all_up


def n8n_api(method, endpoint, data=None):
    """Make n8n API request."""
    if not API_KEY:
        print("ERROR: Set N8N_API_KEY environment variable")
        sys.exit(1)

    url = f"{N8N_URL}/api/v1{endpoint}"
    headers = {
        "X-N8N-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    if data:
        req = urllib.request.Request(url, json.dumps(data).encode(), headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)

    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}


def list_workflows():
    """List all n8n workflows."""
    result = n8n_api("GET", "/workflows")
    if "data" in result:
        print(f"\nn8n Workflows ({len(result['data'])}):")
        print("-" * 60)
        for wf in result["data"]:
            active = "🟢" if wf.get("active") else "🔴"
            print(f"  {active} [{wf['id']}] {wf['name']}")
    else:
        print(f"Error: {result}")


def import_workflows():
    """Import all workflow JSONs."""
    jsons = sorted(WORKFLOW_DIR.glob("0*.json"))
    if not jsons:
        print("No workflow JSONs found!")
        return

    print(f"\nImporting {len(jsons)} workflows...")
    for f in jsons:
        with open(f) as fp:
            wf_data = json.load(fp)

        result = n8n_api("POST", "/workflows", wf_data)
        if "id" in result:
            print(f"  ✅ {f.name} → ID {result['id']}")
            # Activate
            n8n_api("PATCH", f"/workflows/{result['id']}", {"active": True})
        else:
            print(f"  ❌ {f.name}: {result.get('message', result)}")


def list_webhooks():
    """List webhook URLs from workflows."""
    result = n8n_api("GET", "/workflows")
    if "data" not in result:
        print("Cannot fetch workflows")
        return

    print("\nn8n Webhook Endpoints:")
    print("-" * 60)
    for wf in result["data"]:
        for node in wf.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                path = node.get("parameters", {}).get("path", "unknown")
                method = node.get("parameters", {}).get("httpMethod", "POST")
                active = "🟢" if wf.get("active") else "🔴"
                print(f"  {active} {method} {N8N_URL}/webhook/{path}")
                print(f"     Workflow: {wf['name']}")


def trigger_webhook(path, data=None):
    """Trigger a webhook."""
    url = f"{N8N_URL}/webhook/{path}"
    payload = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, payload, {"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("n8n Connector - AI Empire")
        print("Usage:")
        print("  --status      System health check")
        print("  --workflows   List workflows")
        print("  --import-all  Import all workflow JSONs")
        print("  --webhooks    List webhook endpoints")
        print("  --trigger PATH [JSON]  Trigger webhook")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "--status":
        system_status()
    elif cmd == "--workflows":
        list_workflows()
    elif cmd == "--import-all":
        import_workflows()
    elif cmd == "--webhooks":
        list_webhooks()
    elif cmd == "--trigger":
        if len(sys.argv) < 3:
            print("Usage: --trigger <webhook-path> [json-data]")
            sys.exit(1)
        path = sys.argv[2]
        data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = trigger_webhook(path, data)
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {cmd}")
