#!/usr/bin/env python3
"""
AGENT SWARM MASTERCONTROL
Launch and manage the entire autonomous agent army
100% local, 100% free, 24/7 autonomous
"""

import subprocess
import os
import sys
import time
import signal
from typing import List, Dict
import json

class AgentSwarmMasterControl:
    """Master control for launching and managing all agents"""

    def __init__(self):
        self.agents_running: Dict[str, subprocess.Popen] = {}
        self.agent_definitions = [
            {
                "name": "Maestro",
                "script": "maestro_agent.py",
                "description": "Master coordinator & Claude's local extension",
                "critical": True
            },
            {
                "name": "Orchestrator",
                "script": "agent_swarm_orchestrator.py",
                "description": "Main problem detector & router (8 sub-agents)",
                "critical": True
            },
            {
                "name": "AutoDebugger",
                "script": "autonomous_debugger_agent.py",
                "description": "Finds and fixes errors automatically",
                "critical": False
            },
            {
                "name": "CodeOptimizer",
                "script": "code_optimizer_agent.py",
                "description": "Continuously optimizes code",
                "critical": False
            },
        ]

        self.base_path = "/Users/maurice/AIEmpire-Core/.claude/worktrees/cranky-leavitt"

    def check_prerequisites(self) -> bool:
        """Check if all required services are running"""

        print("\n" + "="*70)
        print("🔍 CHECKING PREREQUISITES")
        print("="*70)

        services = {
            "Ollama": ("http://localhost:11434/api/tags", "Ollama LLM"),
            "Redis": ("localhost:6379", "Redis Cache"),
            "PostgreSQL": ("localhost:5432", "PostgreSQL DB"),
        }

        all_ok = True

        for service_name, (endpoint, description) in services.items():
            if ":" in endpoint and not endpoint.startswith("http"):
                # TCP check
                import socket
                host, port = endpoint.split(":")
                try:
                    socket.create_connection((host, int(port)), timeout=2)
                    print(f"✅ {service_name}: UP ({description})")
                except:
                    print(f"❌ {service_name}: DOWN ({description})")
                    all_ok = False
            else:
                # HTTP check
                try:
                    import httpx
                    response = httpx.get(endpoint, timeout=2)
                    print(f"✅ {service_name}: UP ({description})")
                except:
                    print(f"❌ {service_name}: DOWN ({description})")
                    all_ok = False

        return all_ok

    def launch_agent(self, agent: Dict[str, str]) -> bool:
        """Launch a single agent"""

        script_path = os.path.join(self.base_path, agent["script"])

        if not os.path.exists(script_path):
            print(f"❌ {agent['name']}: Script not found ({script_path})")
            return False

        try:
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.base_path,
                preexec_fn=os.setsid  # Create process group
            )

            self.agents_running[agent["name"]] = process
            print(f"✅ {agent['name']}: LAUNCHED (PID: {process.pid})")

            return True

        except Exception as e:
            print(f"❌ {agent['name']}: Failed to launch ({e})")
            return False

    def launch_all_agents(self):
        """Launch entire agent army"""

        print("\n" + "="*70)
        print("🚀 LAUNCHING AGENT ARMY")
        print("="*70)

        for agent in self.agent_definitions:
            print(f"\n📦 Launching {agent['name']}...")
            print(f"   Description: {agent['description']}")

            if not self.launch_agent(agent):
                if agent.get("critical"):
                    print(f"❌ CRITICAL AGENT FAILED - ABORTING")
                    self.shutdown()
                    return False

            time.sleep(2)  # Stagger launches

        return True

    def monitor_agents(self):
        """Monitor and restart failed agents"""

        print("\n" + "="*70)
        print("📊 MONITORING AGENTS (Press Ctrl+C to stop)")
        print("="*70)

        try:
            while True:
                time.sleep(30)  # Check every 30 seconds

                status = self.check_agent_health()

                # Auto-restart critical agents
                for agent_name, agent_info in status.items():
                    if not agent_info["alive"] and agent_info["critical"]:
                        print(f"\n⚠️  Critical agent {agent_name} died, restarting...")

                        # Find agent definition
                        agent_def = next(
                            (a for a in self.agent_definitions if a["name"] == agent_name),
                            None
                        )

                        if agent_def:
                            self.launch_agent(agent_def)
                            time.sleep(2)

                # Print status line
                alive = sum(1 for a in status.values() if a["alive"])
                total = len(status)
                print(f"\r✅ {alive}/{total} agents healthy", end="", flush=True)

        except KeyboardInterrupt:
            print("\n\n⏹️  Shutdown requested")
            self.shutdown()

    def check_agent_health(self) -> Dict[str, Dict]:
        """Check health of all agents"""

        status = {}

        for agent_def in self.agent_definitions:
            agent_name = agent_def["name"]
            process = self.agents_running.get(agent_name)

            if process and process.poll() is None:
                status[agent_name] = {
                    "alive": True,
                    "pid": process.pid,
                    "critical": agent_def.get("critical", False)
                }
            else:
                status[agent_name] = {
                    "alive": False,
                    "critical": agent_def.get("critical", False)
                }

        return status

    def shutdown(self):
        """Graceful shutdown of all agents"""

        print("\n" + "="*70)
        print("🛑 SHUTTING DOWN AGENT ARMY")
        print("="*70)

        for agent_name, process in self.agents_running.items():
            if process.poll() is None:
                print(f"Stopping {agent_name}...")
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.wait(timeout=5)
                except:
                    process.kill()

        print("✅ All agents stopped")
        print("="*70)

    def print_status_dashboard(self):
        """Print ASCII dashboard"""

        status = self.check_agent_health()

        dashboard = """
╔════════════════════════════════════════════════════════════════════════════╗
║                   🚀 AGENT SWARM OPERATIONAL DASHBOARD                    ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  AGENT ARMY STATUS:                                                        ║
║
"""

        for agent_def in self.agent_definitions:
            agent_name = agent_def["name"]
            agent_status = status.get(agent_name, {})

            indicator = "✅" if agent_status.get("alive") else "❌"
            critical = "[CRITICAL]" if agent_status.get("critical") else ""

            dashboard += f"║  {indicator} {agent_name:20} {critical:12} {agent_def['description']:40} ║\n"

        dashboard += """║                                                                            ║
║  CAPABILITIES:                                                             ║
║  • Continuous problem detection & autonomous fixing                       ║
║  • Real-time code optimization (no human needed)                          ║
║  • Self-healing system architecture                                       ║
║  • 24/7 autonomous operation (FREE - local Ollama only)                   ║
║  • Multi-agent coordination & parallel task execution                    ║
║                                                                            ║
║  MODELS USED (All Free & Local):                                         ║
║  • deepseek-r1:8b  (reasoning, debugging)                                ║
║  • qwen2.5-coder:7b (code generation)                                    ║
║  • glm-4.7:flash    (creative problem solving)                           ║
║                                                                            ║
║  COST: €0/month (100% local, no API calls, no subscriptions)             ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

        print(dashboard)

    def run(self):
        """Main program"""

        # Register signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())

        # Check prerequisites
        if not self.check_prerequisites():
            print("\n⚠️  WARNING: Some services are down")
            print("Make sure Ollama, Redis, and PostgreSQL are running:")
            print("  ollama serve")
            print("  redis-server")
            print("  postgres")
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                return

        # Launch all agents
        if not self.launch_all_agents():
            print("\n❌ Failed to launch agent army")
            return

        # Print status
        self.print_status_dashboard()

        # Start monitoring
        self.monitor_agents()

def main():
    mastercontrol = AgentSwarmMasterControl()
    mastercontrol.run()

if __name__ == "__main__":
    main()
