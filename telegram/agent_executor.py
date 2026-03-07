#!/usr/bin/env python3
"""
AGENT EXECUTOR - Ant Protocol Integration
==========================================
Manages communication with:
- 10 local agents (/root/agents/agent-*/agent.py)
- Ant Protocol API (Port 8900)
- Remote command execution
"""

import aiohttp
import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

ANT_PROTOCOL_URL = os.getenv("ANT_PROTOCOL_URL", "http://localhost:8900")
HETZNER_SSH_HOST = os.getenv("HETZNER_SSH_HOST")
HETZNER_SSH_USER = os.getenv("HETZNER_SSH_USER")
HETZNER_SSH_KEY = os.getenv("HETZNER_SSH_KEY")

# Local agent mapping
AGENTS = {
    "agent-01": "revenue_tracking",
    "agent-02": "content_generation",
    "agent-03": "lead_scoring",
    "agent-04": "email_outreach",
    "agent-05": "social_monitoring",
    "agent-06": "competitor_analysis",
    "agent-07": "market_research",
    "agent-08": "campaign_manager",
    "agent-09": "customer_support",
    "agent-10": "data_processor",
}


class AgentExecutor:
    """Manages agent execution and communication"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logger

    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        self.logger.info("✅ Agent Executor initialized")

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    async def execute_via_ant_protocol(
        self,
        task: str,
        agent_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute task via Ant Protocol API
        Routes to: /api/execute endpoint
        """
        try:
            payload = {
                "action": "execute",
                "task": task,
                "agent_id": agent_id,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            self.logger.info(f"🚀 Executing via Ant Protocol: {task[:50]}")

            response = await self.session.post(
                f"{ANT_PROTOCOL_URL}/api/execute",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            )

            if response.status == 200:
                result = await response.json()
                self.logger.info(f"✅ Ant Protocol response: {result}")
                return result
            else:
                error_text = await response.text()
                self.logger.error(f"❌ Ant Protocol error ({response.status}): {error_text}")
                return {
                    "status": "error",
                    "message": f"HTTP {response.status}",
                    "details": error_text
                }

        except asyncio.TimeoutError:
            self.logger.error("⏱️ Ant Protocol timeout")
            return {"status": "timeout", "message": "Request timeout"}
        except Exception as e:
            self.logger.error(f"❌ Ant Protocol error: {e}")
            return {"status": "error", "message": str(e)}

    async def execute_local_agent(
        self,
        agent_num: int,
        command: str
    ) -> Dict[str, Any]:
        """
        Execute local agent via subprocess
        Routes to: /root/agents/agent-*/agent.py
        """
        try:
            agent_id = f"agent-{agent_num:02d}"
            agent_path = f"/root/agents/{agent_id}/agent.py"

            self.logger.info(f"🤖 Executing local agent: {agent_id}")

            # Check if agent exists
            if not os.path.exists(agent_path):
                return {
                    "status": "error",
                    "message": f"Agent not found: {agent_path}",
                    "agent_id": agent_id
                }

            # Execute agent with command
            process = await asyncio.create_subprocess_exec(
                "python3", agent_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send command via stdin
            stdout, stderr = await asyncio.wait_for(
                process.communicate(command.encode()),
                timeout=30
            )

            result = {
                "status": "success" if process.returncode == 0 else "error",
                "agent_id": agent_id,
                "command": command,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else "",
                "exit_code": process.returncode
            }

            self.logger.info(f"✅ Agent {agent_id} completed: exit={process.returncode}")
            return result

        except asyncio.TimeoutError:
            self.logger.error(f"⏱️ Agent {agent_id} timeout")
            return {
                "status": "timeout",
                "agent_id": agent_id,
                "message": "Agent execution timeout"
            }
        except Exception as e:
            self.logger.error(f"❌ Agent error: {e}")
            return {
                "status": "error",
                "agent_id": agent_id,
                "message": str(e)
            }

    async def execute_remote_ssh(
        self,
        command: str,
        target_host: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute command on remote Hetzner server via SSH
        """
        if not HETZNER_SSH_HOST:
            return {
                "status": "error",
                "message": "Hetzner SSH not configured"
            }

        try:
            host = target_host or HETZNER_SSH_HOST
            user = HETZNER_SSH_USER or "root"

            self.logger.info(f"🌐 SSH to {user}@{host}: {command[:50]}")

            # Build SSH command
            ssh_cmd = ["ssh", "-i", HETZNER_SSH_KEY, f"{user}@{host}", command]

            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60
            )

            result = {
                "status": "success" if process.returncode == 0 else "error",
                "host": host,
                "command": command,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else "",
                "exit_code": process.returncode
            }

            self.logger.info(f"✅ SSH command completed: exit={process.returncode}")
            return result

        except asyncio.TimeoutError:
            self.logger.error(f"⏱️ SSH timeout")
            return {
                "status": "timeout",
                "message": "SSH command timeout"
            }
        except Exception as e:
            self.logger.error(f"❌ SSH error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of specific agent"""
        try:
            response = await self.session.get(
                f"{ANT_PROTOCOL_URL}/agents/{agent_id}/status",
                timeout=aiohttp.ClientTimeout(total=10)
            )

            if response.status == 200:
                return await response.json()
            else:
                return {"status": "unreachable", "agent_id": agent_id}

        except Exception as e:
            self.logger.error(f"Status check error: {e}")
            return {"status": "error", "message": str(e)}

    async def get_all_agents_status(self) -> Dict[str, Dict]:
        """Get status of all agents"""
        statuses = {}

        try:
            response = await self.session.get(
                f"{ANT_PROTOCOL_URL}/agents/status",
                timeout=aiohttp.ClientTimeout(total=15)
            )

            if response.status == 200:
                statuses = await response.json()
        except:
            pass

        return statuses

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel"""
        try:
            results = await asyncio.gather(*[
                self.execute_via_ant_protocol(
                    task["command"],
                    task.get("agent_id"),
                    task.get("context")
                )
                for task in tasks
            ], return_exceptions=True)

            return [
                r if isinstance(r, dict) else {"status": "error", "message": str(r)}
                for r in results
            ]

        except Exception as e:
            self.logger.error(f"Batch execution error: {e}")
            return [{"status": "error", "message": str(e)} for _ in tasks]

    async def trigger_agent_by_intent(
        self,
        intent: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Route intent to appropriate agent
        Intent → Agent mapping
        """
        intent_routes = {
            "revenue": {"agent_id": "agent-01", "task": "track_revenue"},
            "content": {"agent_id": "agent-02", "task": "generate_content"},
            "leads": {"agent_id": "agent-03", "task": "score_leads"},
            "outreach": {"agent_id": "agent-04", "task": "send_emails"},
            "social": {"agent_id": "agent-05", "task": "monitor_social"},
            "competitor": {"agent_id": "agent-06", "task": "analyze_competition"},
            "research": {"agent_id": "agent-07", "task": "market_research"},
            "campaign": {"agent_id": "agent-08", "task": "manage_campaign"},
            "support": {"agent_id": "agent-09", "task": "customer_support"},
            "data": {"agent_id": "agent-10", "task": "process_data"},
        }

        route = intent_routes.get(intent.lower())
        if not route:
            return {"status": "error", "message": f"Unknown intent: {intent}"}

        task_payload = {
            "task": route["task"],
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        return await self.execute_via_ant_protocol(
            json.dumps(task_payload),
            route["agent_id"]
        )


async def main():
    """Test agent executor"""
    executor = AgentExecutor()
    await executor.initialize()

    try:
        # Test 1: Get all agents status
        print("📊 Getting agent status...")
        status = await executor.get_all_agents_status()
        print(f"Agents: {json.dumps(status, indent=2)}")

        # Test 2: Execute via Ant Protocol
        print("\n🚀 Testing Ant Protocol execution...")
        result = await executor.execute_via_ant_protocol(
            "Test command from advanced bot"
        )
        print(f"Result: {json.dumps(result, indent=2)}")

        # Test 3: Trigger agent by intent
        print("\n🤖 Testing intent routing...")
        result = await executor.trigger_agent_by_intent("revenue", 123)
        print(f"Result: {json.dumps(result, indent=2)}")

    finally:
        await executor.close()


if __name__ == "__main__":
    asyncio.run(main())
