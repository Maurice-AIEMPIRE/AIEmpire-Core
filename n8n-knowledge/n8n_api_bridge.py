"""
n8n API Bridge - Connect Empire Control Center to n8n.

Full REST API client for programmatic n8n control:
- Workflow management (CRUD, activate, execute)
- Execution monitoring
- Credential management
- Health checks

Integrated into Empire CLI via: python empire.py n8n <command>
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


class N8NApiBridge:
    """Async n8n REST API client for AIEmpire integration."""

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
    ):
        self.base_url = (base_url or os.environ.get("N8N_URL", "http://localhost:5678")).rstrip("/")
        self.api_key = api_key or os.environ.get("N8N_API_KEY", "")
        self.headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    # -- Health --

    async def health(self) -> dict:
        """Check n8n health status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/healthz", timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return {
                        "status": "healthy" if resp.status == 200 else "unhealthy",
                        "code": resp.status,
                        "url": self.base_url,
                    }
        except Exception as e:
            return {"status": "unreachable", "error": str(e), "url": self.base_url}

    # -- Workflows --

    async def list_workflows(self, active_only: bool = False) -> list:
        """List all workflows."""
        data = await self._get("/api/v1/workflows")
        workflows = data.get("data", [])
        if active_only:
            workflows = [w for w in workflows if w.get("active")]
        return workflows

    async def get_workflow(self, workflow_id: str) -> dict:
        """Get a specific workflow by ID."""
        return await self._get(f"/api/v1/workflows/{workflow_id}")

    async def create_workflow(self, name: str, nodes: list = None, connections: dict = None) -> dict:
        """Create a new workflow."""
        payload = {
            "name": name,
            "nodes": nodes or [],
            "connections": connections or {},
            "settings": {"saveDataSuccessExecution": "all"},
        }
        return await self._post("/api/v1/workflows", payload)

    async def update_workflow(self, workflow_id: str, updates: dict) -> dict:
        """Update an existing workflow."""
        return await self._patch(f"/api/v1/workflows/{workflow_id}", updates)

    async def activate_workflow(self, workflow_id: str) -> dict:
        """Activate a workflow."""
        return await self._post(f"/api/v1/workflows/{workflow_id}/activate")

    async def deactivate_workflow(self, workflow_id: str) -> dict:
        """Deactivate a workflow."""
        return await self._post(f"/api/v1/workflows/{workflow_id}/deactivate")

    async def delete_workflow(self, workflow_id: str) -> dict:
        """Delete a workflow."""
        return await self._delete(f"/api/v1/workflows/{workflow_id}")

    async def execute_workflow(self, workflow_id: str, data: dict = None) -> dict:
        """Execute a workflow with optional input data."""
        payload = {}
        if data:
            payload["data"] = data
        return await self._post(f"/api/v1/workflows/{workflow_id}/execute", payload)

    # -- Executions --

    async def list_executions(self, workflow_id: str = None, limit: int = 20) -> list:
        """List workflow executions."""
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        data = await self._get("/api/v1/executions", params=params)
        return data.get("data", [])

    async def get_execution(self, execution_id: str) -> dict:
        """Get a specific execution."""
        return await self._get(f"/api/v1/executions/{execution_id}")

    # -- Credentials --

    async def list_credentials(self) -> list:
        """List all credentials."""
        data = await self._get("/api/v1/credentials")
        return data.get("data", [])

    # -- Deploy Workflow from JSON --

    async def deploy_workflow_json(self, json_path: str) -> dict:
        """Deploy a workflow from a JSON file."""
        path = Path(json_path)
        if not path.exists():
            return {"error": f"File not found: {json_path}"}

        workflow_data = json.loads(path.read_text())
        name = workflow_data.get("name", path.stem)

        # Check if workflow with same name exists
        existing = await self.list_workflows()
        for w in existing:
            if w.get("name") == name:
                # Update existing
                return await self.update_workflow(w["id"], workflow_data)

        # Create new
        return await self.create_workflow(
            name=name,
            nodes=workflow_data.get("nodes", []),
            connections=workflow_data.get("connections", {}),
        )

    async def deploy_all_workflows(self, directory: str = None) -> list:
        """Deploy all workflow JSON files from a directory."""
        dir_path = Path(directory or "n8n-workflows")
        if not dir_path.exists():
            return [{"error": f"Directory not found: {dir_path}"}]

        results = []
        for json_file in sorted(dir_path.glob("*.json")):
            result = await self.deploy_workflow_json(str(json_file))
            results.append({"file": json_file.name, "result": result})

        return results

    # -- Status Dashboard --

    async def dashboard(self) -> dict:
        """Get complete n8n status for Empire dashboard."""
        health = await self.health()

        if health.get("status") != "healthy":
            return {"status": "offline", "health": health}

        workflows = await self.list_workflows()
        recent_executions = await self.list_executions(limit=10)

        active = [w for w in workflows if w.get("active")]
        errors = [e for e in recent_executions if e.get("finished") and not e.get("stoppedAt") and e.get("status") == "error"]

        return {
            "status": "online",
            "url": self.base_url,
            "workflows": {
                "total": len(workflows),
                "active": len(active),
                "inactive": len(workflows) - len(active),
            },
            "executions": {
                "recent": len(recent_executions),
                "errors": len(errors),
            },
            "health": health,
        }

    # -- HTTP Helpers --

    async def _get(self, path: str, params: dict = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}{path}",
                headers=self.headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"HTTP {resp.status}", "body": await resp.text()}

    async def _post(self, path: str, data: dict = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}{path}",
                headers=self.headers,
                json=data or {},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                return {"error": f"HTTP {resp.status}", "body": await resp.text()}

    async def _patch(self, path: str, data: dict = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}{path}",
                headers=self.headers,
                json=data or {},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"HTTP {resp.status}", "body": await resp.text()}

    async def _delete(self, path: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}{path}",
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status in (200, 204):
                    return {"status": "deleted"}
                return {"error": f"HTTP {resp.status}", "body": await resp.text()}


# -- CLI Interface --

async def cli_main():
    """CLI interface for n8n API bridge."""
    import argparse

    parser = argparse.ArgumentParser(description="n8n API Bridge")
    parser.add_argument("command", choices=[
        "health", "status", "workflows", "executions",
        "deploy", "deploy-all", "activate", "deactivate",
        "execute", "credentials",
    ])
    parser.add_argument("--id", help="Workflow or execution ID")
    parser.add_argument("--file", help="JSON file path for deploy")
    parser.add_argument("--dir", help="Directory for deploy-all")
    args = parser.parse_args()

    bridge = N8NApiBridge()

    if args.command == "health":
        result = await bridge.health()
    elif args.command == "status":
        result = await bridge.dashboard()
    elif args.command == "workflows":
        result = await bridge.list_workflows()
    elif args.command == "executions":
        result = await bridge.list_executions(workflow_id=args.id)
    elif args.command == "deploy" and args.file:
        result = await bridge.deploy_workflow_json(args.file)
    elif args.command == "deploy-all":
        result = await bridge.deploy_all_workflows(args.dir)
    elif args.command == "activate" and args.id:
        result = await bridge.activate_workflow(args.id)
    elif args.command == "deactivate" and args.id:
        result = await bridge.deactivate_workflow(args.id)
    elif args.command == "execute" and args.id:
        result = await bridge.execute_workflow(args.id)
    elif args.command == "credentials":
        result = await bridge.list_credentials()
    else:
        print("Missing required argument. Use --help for usage.")
        return

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(cli_main())
