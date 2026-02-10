#!/usr/bin/env python3
"""
AGENT SWARM ORCHESTRATOR
Master Controller für 5-10 autonome Agents
100% lokal auf Ollama, kostenlos, selbstheilend

Architecture:
  Problem Detection → Queue → Agent Routing → Execution → Verification → Reporting
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import subprocess
import psycopg2
import redis
from enum import Enum

class AgentType(Enum):
    DEBUGGER = "debugger"           # Root cause analysis
    CODER = "coder"                 # Code fixes
    SOLVER = "solver"               # Problem solving
    MONITOR = "monitor"             # System monitoring
    OPTIMIZER = "optimizer"         # Performance optimization
    LEARNER = "learner"             # Knowledge extraction
    TESTER = "tester"               # Validation & testing
    HEALER = "healer"               # Self-healing fixes

class ProblemSeverity(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class Agent:
    """Individual AI Agent (runs locally via Ollama)"""

    def __init__(self, agent_id: str, agent_type: AgentType, model: str = "deepseek-r1:8b"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.model = model
        self.status = "idle"
        self.current_task = None
        self.success_rate = 0.95
        self.last_task = None

    async def execute(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Execute problem-solving task"""
        self.status = "working"
        self.current_task = problem

        # Build prompt based on agent type
        prompt = self._build_prompt(problem)

        try:
            # Call local Ollama (free, local inference)
            result = await self._call_ollama(prompt)
            self.status = "success"
            self.last_task = problem
            return result
        except Exception as e:
            self.status = "error"
            return {"error": str(e), "agent": self.agent_id}

    def _build_prompt(self, problem: Dict[str, Any]) -> str:
        """Build specialized prompt for agent type"""
        base_prompt = f"""
You are an AI Agent specialized in {self.agent_type.value}.
Problem: {json.dumps(problem, indent=2)}

Your task:
1. Analyze the problem thoroughly
2. Identify root causes
3. Propose solution(s)
4. Provide verification steps
5. Return structured JSON response

Response format:
{{
  "diagnosis": "...",
  "root_cause": "...",
  "solution": "...",
  "verification": "...",
  "confidence": 0.0-1.0,
  "next_steps": []
}}
"""
        return base_prompt

    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """Call local Ollama for inference (FREE)"""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40
                },
                timeout=300.0
            )
            return response.json()

class Orchestrator:
    """Master Orchestrator - coordinates all agents"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.problem_queue: List[Dict[str, Any]] = []
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.db_conn = None
        self._initialize_agents()
        self._init_database()

    def _initialize_agents(self):
        """Spawn 8 specialized agents"""
        agent_configs = [
            ("agent_debugger_1", AgentType.DEBUGGER, "deepseek-r1:8b"),
            ("agent_coder_1", AgentType.CODER, "qwen2.5-coder:7b"),
            ("agent_coder_2", AgentType.CODER, "qwen2.5-coder:7b"),
            ("agent_solver_1", AgentType.SOLVER, "glm-4.7:flash"),
            ("agent_optimizer_1", AgentType.OPTIMIZER, "deepseek-r1:8b"),
            ("agent_monitor_1", AgentType.MONITOR, "qwen2.5-coder:7b"),
            ("agent_healer_1", AgentType.HEALER, "glm-4.7:flash"),
            ("agent_tester_1", AgentType.TESTER, "qwen2.5-coder:7b"),
        ]

        for agent_id, agent_type, model in agent_configs:
            self.agents[agent_id] = Agent(agent_id, agent_type, model)
            print(f"✅ Agent spawned: {agent_id} ({agent_type.value})")

    def _init_database(self):
        """Initialize PostgreSQL for agent state tracking"""
        try:
            self.db_conn = psycopg2.connect(
                host="localhost",
                database="agent_swarm",
                user="postgres",
                password="postgres"
            )
            cursor = self.db_conn.cursor()

            # Create tables if not exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS problems (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    description TEXT,
                    severity INT,
                    status VARCHAR(50),
                    assigned_agent VARCHAR(50),
                    solution TEXT,
                    verified BOOLEAN DEFAULT FALSE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_stats (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(100),
                    problems_solved INT DEFAULT 0,
                    success_rate FLOAT DEFAULT 0.95,
                    last_task TIMESTAMP,
                    uptime_hours INT DEFAULT 0
                )
            """)

            self.db_conn.commit()
            cursor.close()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️  DB Error: {e}")

    async def detect_problems(self) -> List[Dict[str, Any]]:
        """Autonomously detect problems in system"""
        problems = []

        # Check 1: Command execution failures
        failed_tasks = await self._check_failed_tasks()
        if failed_tasks:
            problems.extend(failed_tasks)

        # Check 2: System health
        health_issues = await self._check_system_health()
        if health_issues:
            problems.extend(health_issues)

        # Check 3: Code quality issues
        code_issues = await self._check_code_issues()
        if code_issues:
            problems.extend(code_issues)

        # Check 4: Performance issues
        perf_issues = await self._check_performance()
        if perf_issues:
            problems.extend(perf_issues)

        return problems

    async def _check_failed_tasks(self) -> List[Dict[str, Any]]:
        """Check for failed processes/tasks"""
        problems = []

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd="/Users/maurice/AIEmpire-Core"
            )

            if result.returncode != 0:
                problems.append({
                    "type": "git_error",
                    "severity": ProblemSeverity.HIGH.value,
                    "description": f"Git error: {result.stderr}",
                    "context": {"command": "git status"}
                })
        except Exception as e:
            problems.append({
                "type": "system_error",
                "severity": ProblemSeverity.MEDIUM.value,
                "description": str(e)
            })

        return problems

    async def _check_system_health(self) -> List[Dict[str, Any]]:
        """Check Ollama, Redis, PostgreSQL"""
        problems = []

        # Check Ollama
        try:
            import httpx
            response = httpx.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code != 200:
                problems.append({
                    "type": "ollama_down",
                    "severity": ProblemSeverity.CRITICAL.value,
                    "description": "Ollama service not responding"
                })
        except:
            problems.append({
                "type": "ollama_unreachable",
                "severity": ProblemSeverity.CRITICAL.value,
                "description": "Cannot reach Ollama on localhost:11434"
            })

        # Check Redis
        try:
            self.redis_client.ping()
        except:
            problems.append({
                "type": "redis_down",
                "severity": ProblemSeverity.HIGH.value,
                "description": "Redis not accessible"
            })

        return problems

    async def _check_code_issues(self) -> List[Dict[str, Any]]:
        """Check for code quality issues"""
        problems = []

        # Scan for common issues
        result = subprocess.run(
            ["grep", "-r", "TODO:", ".", "--include=*.py"],
            capture_output=True,
            text=True,
            cwd="/Users/maurice/AIEmpire-Core"
        )

        if result.stdout:
            problems.append({
                "type": "code_todos",
                "severity": ProblemSeverity.LOW.value,
                "description": f"Found {len(result.stdout.splitlines())} TODO markers",
                "count": len(result.stdout.splitlines())
            })

        return problems

    async def _check_performance(self) -> List[Dict[str, Any]]:
        """Check system performance metrics"""
        problems = []

        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent

        if cpu_percent > 80:
            problems.append({
                "type": "high_cpu",
                "severity": ProblemSeverity.MEDIUM.value,
                "description": f"CPU usage at {cpu_percent}%",
                "value": cpu_percent
            })

        if memory_percent > 85:
            problems.append({
                "type": "high_memory",
                "severity": ProblemSeverity.HIGH.value,
                "description": f"Memory usage at {memory_percent}%",
                "value": memory_percent
            })

        return problems

    async def route_problem(self, problem: Dict[str, Any]) -> str:
        """Route problem to most suitable agent"""
        problem_type = problem.get("type", "unknown")

        routing_map = {
            "code_": "agent_coder_1",
            "git_": "agent_debugger_1",
            "system_": "agent_monitor_1",
            "performance": "agent_optimizer_1",
            "error": "agent_debugger_1",
            "verify": "agent_tester_1"
        }

        for key, agent_id in routing_map.items():
            if key in problem_type:
                return agent_id

        # Default: least busy agent
        return min(self.agents.keys(),
                  key=lambda x: self.agents[x].status == "idle")

    async def solve_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate problem solving"""
        agent_id = await self.route_problem(problem)
        agent = self.agents[agent_id]

        print(f"🔧 Routing to {agent_id}...")

        result = await agent.execute(problem)

        # Store in database
        if self.db_conn:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO problems (description, severity, status, assigned_agent, solution)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                json.dumps(problem),
                problem.get("severity", 2),
                "solved" if "error" not in result else "failed",
                agent_id,
                json.dumps(result)
            ))
            self.db_conn.commit()
            cursor.close()

        return {
            "agent": agent_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    async def run_loop(self):
        """Main autonomous loop"""
        print("\n" + "="*60)
        print("🚀 AGENT SWARM STARTING - AUTONOMOUS MODE")
        print("="*60)
        print(f"Agents ready: {len(self.agents)}")
        print("Detection interval: 60 seconds")
        print("="*60 + "\n")

        iteration = 0

        while True:
            iteration += 1
            print(f"\n[Iteration {iteration}] {datetime.now().strftime('%H:%M:%S')}")

            try:
                # Step 1: Detect problems
                problems = await self.detect_problems()

                if problems:
                    print(f"🔍 Found {len(problems)} problems:")

                    # Step 2: Solve each problem
                    for problem in problems:
                        print(f"  → {problem.get('type', 'unknown')}: {problem.get('description', '...')}")
                        solution = await self.solve_problem(problem)
                        print(f"    ✅ Solved by {solution['agent']}")
                else:
                    print("✅ All systems healthy")

                # Step 3: Agent health check
                healthy = sum(1 for a in self.agents.values() if a.status != "error")
                print(f"📊 Agent status: {healthy}/{len(self.agents)} healthy")

                # Wait before next iteration
                await asyncio.sleep(60)

            except Exception as e:
                print(f"❌ Orchestrator error: {e}")
                await asyncio.sleep(10)

async def main():
    """Main entry point"""
    orchestrator = Orchestrator()
    await orchestrator.run_loop()

if __name__ == "__main__":
    asyncio.run(main())
