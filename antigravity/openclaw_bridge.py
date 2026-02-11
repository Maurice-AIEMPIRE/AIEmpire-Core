#!/usr/bin/env python3
"""
OpenClaw-Antigravity Bridge
============================
Exposes the 4 Antigravity Agents (Architect, Fixer, Coder, QA) as OpenClaw-compatible agents.
Allows OpenClaw to dispatch tasks to Antigravity's specialized local models.

Usage:
    # Register agents with OpenClaw
    python antigravity/openclaw_bridge.py register

    # Start bridge server (webhook endpoint for OpenClaw)
    python antigravity/openclaw_bridge.py serve

    # Test an agent directly
    python antigravity/openclaw_bridge.py test architect "Design a plugin system"
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from aiohttp import web

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from antigravity.config import AGENTS, AgentConfig
from antigravity.godmode_router import GodmodeRouter

# OpenClaw Bridge Config
BRIDGE_PORT = 18790  # One port above OpenClaw
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"
OPENCLAW_AGENTS_DIR = Path.home() / ".openclaw" / "agents"

# Agent Metadata for OpenClaw
AGENT_METADATA = {
    "architect": {
        "name": "Antigravity Architect",
        "description": "Repository structure, API design, refactoring decisions, architecture documentation",
        "category": "development",
        "tags": ["architecture", "design", "refactoring", "api"],
        "model": "ollama/qwen2.5-coder:7b",
        "capabilities": ["analyze", "design", "document"],
    },
    "fixer": {
        "name": "Antigravity Fixer",
        "description": "Bug fixes, import errors, tracebacks, edge cases, dependency issues",
        "category": "development",
        "tags": ["bugfix", "errors", "debugging", "hotfix"],
        "model": "ollama/qwen2.5-coder:7b",
        "capabilities": ["fix", "debug", "patch"],
    },
    "coder": {
        "name": "Antigravity Coder",
        "description": "Feature implementation, rapid prototyping, utility functions, code generation",
        "category": "development",
        "tags": ["feature", "implementation", "coding", "development"],
        "model": "ollama/qwen2.5-coder:7b",
        "capabilities": ["implement", "code", "prototype"],
    },
    "qa": {
        "name": "Antigravity QA",
        "description": "Code review, testing, lint checks, security review, regression testing",
        "category": "quality",
        "tags": ["qa", "testing", "review", "quality"],
        "model": "ollama/deepseek-r1:8b",
        "capabilities": ["review", "test", "validate"],
    },
}


class OpenClawBridge:
    """Bridge between OpenClaw and Antigravity agents."""

    def __init__(self):
        self.router = GodmodeRouter()
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Setup HTTP routes for OpenClaw webhook integration."""
        self.app.router.add_get("/", self.handle_root)
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_post("/agent/{agent_key}", self.handle_agent_request)
        self.app.router.add_get("/agents", self.handle_list_agents)

    async def handle_root(self, request):
        """Root endpoint - bridge info."""
        return web.json_response({
            "service": "OpenClaw-Antigravity Bridge",
            "version": "1.0.0",
            "agents": list(AGENT_METADATA.keys()),
            "endpoints": {
                "health": "/health",
                "agents": "/agents",
                "execute": "/agent/{agent_key} (POST)",
            }
        })

    async def handle_health(self, request):
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "ollama": await self._check_ollama(),
            "agents": len(AGENTS)
        })

    async def _check_ollama(self) -> bool:
        """Check if Ollama is running."""
        try:
            from antigravity.ollama_client import get_client
            client = get_client()
            return client.health_check()
        except Exception:
            return False

    async def handle_list_agents(self, request):
        """List all available Antigravity agents."""
        agents = []
        for key, config in AGENTS.items():
            meta = AGENT_METADATA[key]
            agents.append({
                "id": key,
                "name": meta["name"],
                "description": meta["description"],
                "model": config.model,
                "category": meta["category"],
                "tags": meta["tags"],
                "capabilities": meta["capabilities"],
            })
        return web.json_response({"agents": agents})

    async def handle_agent_request(self, request):
        """
        Handle agent execution request from OpenClaw.

        Expected POST body:
        {
            "prompt": "Task description",
            "context": {"key": "value"},
            "task_id": "optional-task-id"
        }
        """
        agent_key = request.match_info["agent_key"]

        if agent_key not in AGENTS:
            return web.json_response(
                {"error": f"Unknown agent: {agent_key}"},
                status=404
            )

        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON body"},
                status=400
            )

        prompt = data.get("prompt", "")
        if not prompt:
            return web.json_response(
                {"error": "Missing 'prompt' field"},
                status=400
            )

        context = data.get("context", {})
        task_id = data.get("task_id", f"openclaw-{agent_key}")

        # Add task_id to context
        context["task_id"] = task_id
        context["source"] = "openclaw"

        # Execute via Antigravity router
        try:
            result = await self.router.execute_task(agent_key, prompt, context)

            return web.json_response({
                "success": result.get("success", False),
                "agent": result.get("agent"),
                "model": result.get("model"),
                "output": result.get("output", ""),
                "error": result.get("error", ""),
                "branch": result.get("branch", ""),
            })

        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def start_server(self, port: int = BRIDGE_PORT):
        """Start the bridge HTTP server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", port)
        await site.start()

        print(f"🌉 OpenClaw-Antigravity Bridge running on http://127.0.0.1:{port}")
        print(f"📋 Available agents: {', '.join(AGENTS.keys())}")
        print(f"\nEndpoints:")
        print(f"  Health: http://127.0.0.1:{port}/health")
        print(f"  Agents: http://127.0.0.1:{port}/agents")
        print(f"  Execute: POST http://127.0.0.1:{port}/agent/{{agent_key}}")
        print(f"\nPress Ctrl+C to stop")

        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await runner.cleanup()


def register_agents():
    """
    Register Antigravity agents with OpenClaw.
    Creates agent definition files in ~/.openclaw/agents/
    """
    print("📝 Registering Antigravity agents with OpenClaw...")

    # Ensure agents directory exists
    OPENCLAW_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    registered = []
    for agent_key, agent_config in AGENTS.items():
        meta = AGENT_METADATA[agent_key]

        # Create OpenClaw agent definition
        agent_def = {
            "id": f"antigravity-{agent_key}",
            "name": meta["name"],
            "description": meta["description"],
            "category": meta["category"],
            "tags": meta["tags"],
            "provider": "custom",
            "endpoint": f"http://127.0.0.1:{BRIDGE_PORT}/agent/{agent_key}",
            "model": agent_config.model,
            "temperature": agent_config.temperature,
            "max_tokens": agent_config.max_tokens,
            "system_prompt": agent_config.system_prompt,
            "capabilities": meta["capabilities"],
        }

        # Write to file
        agent_file = OPENCLAW_AGENTS_DIR / f"antigravity-{agent_key}.json"
        with open(agent_file, "w") as f:
            json.dump(agent_def, f, indent=2)

        print(f"  ✅ {meta['name']} → {agent_file.name}")
        registered.append(agent_key)

    print(f"\n✨ Registered {len(registered)} agents:")
    for key in registered:
        print(f"  - antigravity-{key}")

    print(f"\n💡 Next steps:")
    print(f"  1. Start bridge: python antigravity/openclaw_bridge.py serve")
    print(f"  2. Restart OpenClaw if running")
    print(f"  3. Use agents via OpenClaw interface or API")


async def test_agent(agent_key: str, prompt: str):
    """Test an agent directly."""
    if agent_key not in AGENTS:
        print(f"❌ Unknown agent: {agent_key}")
        print(f"Available: {', '.join(AGENTS.keys())}")
        return

    print(f"🧪 Testing {AGENTS[agent_key].name}...")
    print(f"📝 Prompt: {prompt}")
    print()

    router = GodmodeRouter()
    result = await router.execute_task(
        agent_key,
        prompt,
        {"task_id": "test", "source": "cli"}
    )

    print("=" * 60)
    print(f"🤖 {result['agent']} Response:")
    print("=" * 60)
    print(result["output"])

    if result.get("error"):
        print(f"\n⚠️  Error: {result['error']}")

    print(f"\n✅ Branch: {result.get('branch', 'N/A')}")


async def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("""
🌉 OpenClaw-Antigravity Bridge

Commands:
  register    Register Antigravity agents with OpenClaw
  serve       Start bridge HTTP server (default port: 18790)
  test <agent> <prompt>  Test an agent directly

Agents:
  architect   Repository structure, API design, refactoring
  fixer       Bug fixes, import errors, tracebacks
  coder       Feature implementation, prototyping
  qa          Code review, testing, quality checks

Examples:
  python antigravity/openclaw_bridge.py register
  python antigravity/openclaw_bridge.py serve
  python antigravity/openclaw_bridge.py test architect "Design a plugin system"
""")
        sys.exit(1)

    command = sys.argv[1]

    if command == "register":
        register_agents()

    elif command == "serve":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else BRIDGE_PORT
        bridge = OpenClawBridge()
        await bridge.start_server(port)

    elif command == "test":
        if len(sys.argv) < 4:
            print("❌ Usage: test <agent> <prompt>")
            sys.exit(1)

        agent_key = sys.argv[2]
        prompt = " ".join(sys.argv[3:])
        await test_agent(agent_key, prompt)

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
