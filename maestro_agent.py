#!/usr/bin/env python3
"""
MAESTRO AGENT - Bridge between Claude and Local Agent Army
Interprets Claude requests and routes to appropriate agents
Executes complex multi-step tasks autonomously
"""

import asyncio
import json
import subprocess
from typing import Dict, List, Any
import httpx

class MaestroAgent:
    """Maestro coordinates between Claude and local agents"""

    def __init__(self):
        self.model = "glm-4.7:flash"
        self.ollama_url = "http://localhost:11434/api/generate"
        self.task_queue: List[Dict[str, Any]] = []
        self.completed_tasks = 0

    async def listen_for_claude_commands(self) -> List[Dict[str, Any]]:
        """Listen for commands from Claude (via file, webhook, etc)"""
        commands = []

        # Check for command file
        try:
            with open("/tmp/claude_commands.jsonl", "r") as f:
                for line in f:
                    if line.strip():
                        commands.append(json.loads(line))

            # Clear after reading
            with open("/tmp/claude_commands.jsonl", "w") as f:
                f.write("")

        except FileNotFoundError:
            pass

        return commands

    async def interpret_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret Claude's command and plan execution"""

        prompt = f"""
You are the Maestro Agent - interpreter of high-level commands from Claude.

Claude's Command:
{json.dumps(command, indent=2)}

Your job:
1. Understand the goal
2. Break down into subtasks
3. Assign to appropriate agents (debugger, coder, optimizer, monitor)
4. Plan execution order (parallel vs sequential)
5. Return execution plan

Available agents:
- debugger: fixes errors and bugs
- coder: writes/modifies code
- optimizer: improves performance
- monitor: checks system health
- solver: general problem solving

Return JSON plan:
{{
  "goal": "...",
  "subtasks": [
    {{"agent": "debugger|coder|optimizer|monitor|solver",
      "task": "...",
      "priority": 0-10,
      "parallel": true/false}}
  ],
  "estimated_time": "X minutes",
  "success_criteria": "..."
}}
"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.7
                    },
                    timeout=300.0
                )

                result = response.json()
                response_text = result.get("response", "")

                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())

                return {"error": "Could not parse plan"}

        except Exception as e:
            return {"error": str(e)}

    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multi-step plan"""

        results = {
            "goal": plan.get("goal"),
            "subtasks_completed": 0,
            "total_subtasks": len(plan.get("subtasks", [])),
            "status": "executing",
            "results": []
        }

        subtasks = sorted(
            plan.get("subtasks", []),
            key=lambda x: x.get("priority", 5),
            reverse=True
        )

        for subtask in subtasks:
            agent_type = subtask.get("agent")
            task_description = subtask.get("task")

            print(f"\n📋 Executing with {agent_type}: {task_description}")

            # Call appropriate agent
            result = await self._execute_with_agent(
                agent_type,
                task_description
            )

            results["results"].append({
                "agent": agent_type,
                "task": task_description,
                "result": result,
                "success": "error" not in result
            })

            if result.get("success"):
                results["subtasks_completed"] += 1

        results["status"] = "completed"
        self.completed_tasks += 1

        return results

    async def _execute_with_agent(
        self,
        agent_type: str,
        task: str
    ) -> Dict[str, Any]:
        """Execute task with specific agent"""

        # Map agent type to execution
        agent_executors = {
            "debugger": self._execute_debugger,
            "coder": self._execute_coder,
            "optimizer": self._execute_optimizer,
            "monitor": self._execute_monitor,
            "solver": self._execute_solver
        }

        executor = agent_executors.get(agent_type)

        if executor:
            return await executor(task)
        else:
            return {"error": f"Unknown agent type: {agent_type}"}

    async def _execute_debugger(self, task: str) -> Dict[str, Any]:
        """Execute with debugger agent"""
        print(f"  🐛 Debugger working on: {task}")

        # Would call autonomous_debugger_agent.py
        result = subprocess.run(
            ["python3", "/Users/maurice/AIEmpire-Core/.claude/worktrees/cranky-leavitt/autonomous_debugger_agent.py"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {"error": result.stderr}

    async def _execute_coder(self, task: str) -> Dict[str, Any]:
        """Execute with coder agent"""
        print(f"  💻 Coder working on: {task}")

        # Generate code using Ollama
        prompt = f"Write Python code to: {task}\n\nReturn only clean, production-ready code."

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": "qwen2.5-coder:7b",
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.3
                    },
                    timeout=300.0
                )

                code = response.json().get("response", "")
                return {"status": "success", "code": code}

        except Exception as e:
            return {"error": str(e)}

    async def _execute_optimizer(self, task: str) -> Dict[str, Any]:
        """Execute with optimizer agent"""
        print(f"  ⚡ Optimizer working on: {task}")

        result = subprocess.run(
            ["python3", "/Users/maurice/AIEmpire-Core/.claude/worktrees/cranky-leavitt/code_optimizer_agent.py"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {"error": result.stderr}

    async def _execute_monitor(self, task: str) -> Dict[str, Any]:
        """Execute health check"""
        print(f"  📊 Monitor checking: {task}")

        checks = {}

        # Check Ollama
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags", timeout=5)
                checks["ollama"] = "UP" if response.status_code == 200 else "DOWN"
        except:
            checks["ollama"] = "DOWN"

        # Check Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            checks["redis"] = "UP"
        except:
            checks["redis"] = "DOWN"

        # Check PostgreSQL
        try:
            import psycopg2
            conn = psycopg2.connect(host='localhost', user='postgres')
            conn.close()
            checks["postgres"] = "UP"
        except:
            checks["postgres"] = "DOWN"

        return {"status": "success", "checks": checks}

    async def _execute_solver(self, task: str) -> Dict[str, Any]:
        """Execute general problem solver"""
        print(f"  🎯 Solver working on: {task}")

        prompt = f"""
Solve this problem step by step:

{task}

Provide:
1. Problem analysis
2. Solution approach
3. Implementation steps
4. Verification method

Be concise and practical.
"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.7
                    },
                    timeout=300.0
                )

                solution = response.json().get("response", "")
                return {"status": "success", "solution": solution}

        except Exception as e:
            return {"error": str(e)}

    async def report_status(self) -> Dict[str, Any]:
        """Generate status report"""
        return {
            "maestro_status": "operational",
            "tasks_completed": self.completed_tasks,
            "queue_size": len(self.task_queue),
            "timestamp": asyncio.get_event_loop().time()
        }

    async def run(self):
        """Main maestro loop"""

        print("\n" + "="*60)
        print("🎼 MAESTRO AGENT - Claude's Local Extension")
        print("="*60)
        print("Listening for Claude commands...")
        print("="*60 + "\n")

        iteration = 0

        while True:
            iteration += 1

            try:
                # Listen for Claude commands
                commands = await self.listen_for_claude_commands()

                if commands:
                    print(f"\n[Iteration {iteration}] Received {len(commands)} commands from Claude")

                    for command in commands:
                        print(f"\n🎼 Processing: {command.get('description', 'unknown')}")

                        # Interpret command
                        plan = await self.interpret_command(command)

                        if "error" not in plan:
                            # Execute plan
                            result = await self.execute_plan(plan)
                            print(f"✅ Completed {result['subtasks_completed']}/{result['total_subtasks']} subtasks")
                        else:
                            print(f"❌ Could not plan: {plan['error']}")

                else:
                    # Report status every minute
                    if iteration % 6 == 0:
                        status = await self.report_status()
                        print(f"✅ Maestro running. Tasks: {status['tasks_completed']}")

                await asyncio.sleep(10)

            except Exception as e:
                print(f"❌ Maestro error: {e}")
                await asyncio.sleep(10)

async def main():
    maestro = MaestroAgent()
    await maestro.run()

if __name__ == "__main__":
    asyncio.run(main())
