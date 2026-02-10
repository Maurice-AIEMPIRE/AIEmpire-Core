"""
4-Model Godmode Programmer Router
Verteilt Tasks an spezialisierte lokale Modelle
"""

import asyncio
import json
import subprocess
import sys
from antigravity.config import AGENTS
from typing import Any, Optional


class GodmodeRouter:
    def __init__(self) -> None:
        self.agents = AGENTS

    async def route_task(self, task: dict[str, Any]) -> str:
        """Route task to appropriate agent"""
        task_type = task.get("type", "code").lower()
        prompt = task.get("prompt", "").lower()

        # Routing Logic
        if any(kw in task_type or kw in prompt for kw in ["architecture", "refactor", "design", "structure"]):
            agent = "architect"
        elif any(kw in task_type or kw in prompt for kw in ["bug", "error", "fix", "import", "traceback"]):
            agent = "fixer"
        elif any(kw in task_type or kw in prompt for kw in ["test", "qa", "review", "lint", "check"]):
            agent = "qa"
        else:
            agent = "coder"

        return agent

    async def execute_task(
        self, agent_key: str, prompt: str, context: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """Execute task with specific agent"""
        from antigravity.ollama_client import get_client
        
        agent = self.agents[agent_key]
        client = get_client()

        # Create branch
        task_id = context.get("task_id", "task") if context else "task"
        branch_name = f"{agent.branch_prefix}/{task_id}"

        # Check if we're in a git repo
        git_check = await asyncio.to_thread(subprocess.run, ["git", "rev-parse", "--git-dir"], capture_output=True)
        if git_check.returncode == 0:
            # Create branch (ignore if exists)
            await asyncio.to_thread(
                subprocess.run,
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
            )

        print(f"\n🤖 {agent.name} ({agent.model}) is working on task...")
        print(f"📋 Task: {prompt[:100]}...")

        # Execute via optimized OllamaClient
        try:
            # Run in thread executor to avoid blocking implementation details
            response = await asyncio.to_thread(
                client.chat,
                agent=agent,
                user_message=prompt,
                context=json.dumps(context or {}, indent=2)
            )
            
            output = response.get("content", "")
            if not output and response.get("raw_response"):
                # Fallback if content key missing
                output = str(response["raw_response"])

            return {
                "agent": agent.name,
                "model": agent.model,
                "branch": branch_name,
                "output": output,
                "error": "",
                "success": True,
            }
            
        except Exception as e:
            return {
                "agent": agent.name,
                "model": agent.model,
                "branch": branch_name,
                "output": "",
                "error": f"Error executing task: {str(e)}",
                "success": False,
            }

    async def run_parallel_swarm(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run multiple agents in parallel"""
        print(f"\n🚀 Starting Godmode Swarm with {len(tasks)} tasks...")

        async def process_task(task: dict[str, Any]) -> dict[str, Any]:
            agent = await self.route_task(task)
            print(f"  → Routing '{task.get('type', 'task')}' to {AGENTS[agent].name}")
            return await self.execute_task(agent, str(task["prompt"]), task.get("context"))

        results = list(await asyncio.gather(*[process_task(task) for task in tasks]))

        print(f"\n✅ Swarm completed {len(results)} tasks")
        return results


# CLI Interface
async def main() -> None:
    router = GodmodeRouter()

    if len(sys.argv) < 2:
        print("""
🤖 Godmode Router - 4-Model Parallel AI Programmer

Usage:
  python godmode_router.py <task_type> <prompt>

Task Types:
  - architecture: Design, refactoring, structure
  - fix: Bug fixes, errors, imports
  - code: Feature implementation
  - qa: Tests, reviews, quality checks

Examples:
  python godmode_router.py fix "Fix all import errors in antigravity/"
  python godmode_router.py architecture "Design a plugin system for agents"
  python godmode_router.py code "Add logging to empire_launch.py"
  python godmode_router.py qa "Review antigravity/core.py for bugs"

Agents:
  - Architect (qwen2.5-coder:14b): Structure, APIs, Refactoring
  - Fixer (qwen2.5-coder:7b): Bugs, Tracebacks, Imports
  - Coder (qwen2.5-coder:7b): Feature Implementation
  - QA (deepseek-r1:7b): Tests, Lint, Review
""")
        sys.exit(1)

    task: dict[str, Any] = {
        "type": sys.argv[1],
        "prompt": " ".join(sys.argv[2:]),
        "context": {"task_id": f"cli-{sys.argv[1]}"},
    }

    agent_key = await router.route_task(task)
    agent = AGENTS[agent_key]

    print(f"\n🎯 Routing to: {agent.name} ({agent.model})")
    print(f"📝 Role: {agent.role}")

    result = await router.execute_task(agent_key, str(task["prompt"]), task.get("context"))

    print(f"\n{'=' * 60}")
    print(f"🤖 {result['agent']} Response:")
    print(f"{'=' * 60}")
    print(result["output"])

    if result["error"]:
        print("\n⚠️  Errors:")
        print(result["error"])

    print(f"\n{'=' * 60}")
    print(f"✅ Task completed on branch: {result['branch']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
