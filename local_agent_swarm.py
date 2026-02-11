#!/usr/bin/env python3
"""
🔥 LOCAL AGENT SWARM - Production Ready
Maximum Power Edition: 1000+ Agents
"""

import asyncio
import json
import time
import psutil
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sys

try:
    import ollama
except ImportError:
    print("ERROR: pip install ollama --break-system-packages")
    sys.exit(1)

class AgentRole(Enum):
    COORDINATOR = "coordinator"
    MANAGER = "manager"
    WORKER = "worker"
    SPECIALIST_CODE = "specialist_code"
    SPECIALIST_WRITE = "specialist_write"
    SPECIALIST_ANALYSIS = "specialist_analysis"
    QUALITY_GATE = "quality_gate"

@dataclass
class Agent:
    id: str
    role: AgentRole
    model: str
    task_count: int = 0
    success_rate: float = 1.0
    total_time: float = 0.0

    async def execute_task(self, task: str, context: str = "") -> Dict[str, Any]:
        """Execute task with model - optimized for speed"""
        start = time.time()
        try:
            # Determine temperature by role
            temp = 0.5 if self.role == AgentRole.WORKER else 0.3

            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'user', 'content': f"{context}\n\nTask: {task}"}
                ],
                stream=False,
                options={
                    'temperature': temp,
                    'num_ctx': 1024,  # Reduced for speed
                    'num_predict': 256,  # Max tokens
                }
            )

            elapsed = time.time() - start
            self.task_count += 1
            self.total_time += elapsed

            return {
                'status': 'success',
                'agent_id': self.id,
                'output': response['message']['content'],
                'model': self.model,
                'role': self.role.value,
                'exec_time': elapsed
            }
        except Exception as e:
            self.success_rate *= 0.95
            return {
                'status': 'error',
                'agent_id': self.id,
                'error': str(e),
                'model': self.model
            }

class LocalAgentSwarm:
    def __init__(self, max_workers: int = 100, max_tasks: int = 1000):
        self.max_workers = max_workers
        self.max_tasks = max_tasks
        self.agents: Dict[str, Agent] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: List[Dict] = []
        self.start_time = time.time()

        # Models rotation - only quantized
        self.worker_models = ['phi:q4', 'tinyllama:q4']
        self.specialist_models = {
            'code': 'neural-chat:q4',
            'write': 'neural-chat:q4',
            'analysis': 'llama2:q4'
        }
        self.quality_model = 'llama2:q4'

    async def initialize_agents(self):
        """Create agent pool"""
        print(f"\n🤖 Initializing {self.max_workers} agents...")

        agent_id = 0

        # 1 Coordinator
        self.agents['coordinator-0'] = Agent(
            id='coordinator-0',
            role=AgentRole.COORDINATOR,
            model='phi:q4'
        )
        agent_id += 1

        # 10 Managers
        for i in range(10):
            self.agents[f'manager-{i}'] = Agent(
                id=f'manager-{i}',
                role=AgentRole.MANAGER,
                model='neural-chat:q4'
            )
            agent_id += 1

        # 20 Specialists each
        for i in range(20):
            self.agents[f'specialist-code-{i}'] = Agent(
                id=f'specialist-code-{i}',
                role=AgentRole.SPECIALIST_CODE,
                model=self.specialist_models['code']
            )
            self.agents[f'specialist-write-{i}'] = Agent(
                id=f'specialist-write-{i}',
                role=AgentRole.SPECIALIST_WRITE,
                model=self.specialist_models['write']
            )
            self.agents[f'specialist-analysis-{i}'] = Agent(
                id=f'specialist-analysis-{i}',
                role=AgentRole.SPECIALIST_ANALYSIS,
                model=self.specialist_models['analysis']
            )
            agent_id += 3

        # Rest = Workers (fast execution)
        worker_count = self.max_workers - agent_id
        for i in range(worker_count):
            model = self.worker_models[i % len(self.worker_models)]
            self.agents[f'worker-{i}'] = Agent(
                id=f'worker-{i}',
                role=AgentRole.WORKER,
                model=model
            )

        print(f"✓ {len(self.agents)} agents initialized")
        print(f"  Coordinator: 1")
        print(f"  Managers: 10")
        print(f"  Specialists: 60")
        print(f"  Workers: {worker_count}")

    async def worker_loop(self, worker_id: int):
        """Worker loop - process tasks from queue"""
        while not self.task_queue.empty():
            try:
                task = self.task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            # Select best agent
            agent = self._select_agent(task)

            # Execute
            result = await agent.execute_task(
                task['task'],
                task.get('context', '')
            )

            # Store result
            self.results.append(result)
            self.task_queue.task_done()

            # Progress indicator
            if len(self.results) % 50 == 0:
                print(f"  ✓ {len(self.results)} tasks completed")

    def _select_agent(self, task: Dict) -> Agent:
        """Select best agent for task type"""
        task_type = task.get('type', 'general')

        # Route to specialist
        if task_type == 'code':
            candidates = [a for a in self.agents.values()
                        if a.role == AgentRole.SPECIALIST_CODE]
        elif task_type == 'write':
            candidates = [a for a in self.agents.values()
                        if a.role == AgentRole.SPECIALIST_WRITE]
        elif task_type == 'analysis':
            candidates = [a for a in self.agents.values()
                        if a.role == AgentRole.SPECIALIST_ANALYSIS]
        else:
            candidates = [a for a in self.agents.values()
                        if a.role == AgentRole.WORKER]

        # Return agent with best success rate
        if candidates:
            return max(candidates, key=lambda a: (a.success_rate, -a.task_count))
        return list(self.agents.values())[0]

    async def process_tasks(self, tasks: List[Dict], num_workers: int = 10) -> Dict:
        """Process task batch in parallel"""
        print(f"\n⚙️  Processing {len(tasks)} tasks...")
        self.start_time = time.time()
        self.results = []

        # Queue all tasks
        for task in tasks[:self.max_tasks]:
            await self.task_queue.put(task)

        # Run workers in parallel
        num_workers = min(num_workers, len(self.agents) // 2)
        workers = [
            self.worker_loop(i)
            for i in range(num_workers)
        ]

        await asyncio.gather(*workers)

        # Calculate stats
        elapsed = time.time() - self.start_time
        successful = sum(1 for r in self.results if r['status'] == 'success')
        throughput = len(self.results) / elapsed if elapsed > 0 else 0

        return {
            'tasks_completed': len(self.results),
            'successful': successful,
            'failed': len(self.results) - successful,
            'time_elapsed': f"{elapsed:.2f}s",
            'throughput': f"{throughput:.1f} tasks/sec",
            'success_rate': f"{successful/len(self.results)*100:.1f}%" if self.results else "0%",
            'agents_used': len(set(r.get('agent_id') for r in self.results)),
            'avg_exec_time': f"{sum(r.get('exec_time', 0) for r in self.results)/len(self.results):.2f}s" if self.results else "0s"
        }

    def get_stats(self) -> Dict:
        """Get swarm statistics"""
        return {
            'total_agents': len(self.agents),
            'agents_by_role': {
                role.value: len([a for a in self.agents.values() if a.role == role])
                for role in AgentRole
            },
            'total_tasks_completed': sum(a.task_count for a in self.agents.values()),
            'avg_success_rate': f"{sum(a.success_rate for a in self.agents.values())/len(self.agents)*100:.1f}%",
            'models_used': list(set(a.model for a in self.agents.values())),
            'ram_usage': f"{psutil.virtual_memory().percent:.1f}%",
            'ram_available': f"{psutil.virtual_memory().available / (1024**3):.2f}GB"
        }

async def main():
    """Demo execution"""
    print("="*60)
    print("🔥 LOCAL AGENT SWARM - DEMO")
    print("="*60)

    # Create swarm
    swarm = LocalAgentSwarm(max_workers=100)
    await swarm.initialize_agents()

    # Example tasks
    tasks = []

    # Code generation
    for i in range(25):
        tasks.append({
            'task': f'Write Python function #{i}',
            'type': 'code',
            'context': 'Fast, optimized code only'
        })

    # Content generation
    for i in range(25):
        tasks.append({
            'task': f'Write about topic #{i}',
            'type': 'write',
            'context': 'Concise, engaging'
        })

    # Analysis
    for i in range(50):
        tasks.append({
            'task': f'Analyze item #{i}',
            'type': 'analysis',
            'context': 'Quick analysis'
        })

    # Process
    stats = await swarm.process_tasks(tasks, num_workers=10)

    print("\n" + "="*60)
    print("EXECUTION RESULTS")
    print("="*60)
    for key, value in stats.items():
        print(f"{key:<20}: {value}")

    print("\n" + "="*60)
    print("SWARM STATUS")
    print("="*60)
    swarm_stats = swarm.get_stats()
    for key, value in swarm_stats.items():
        print(f"{key:<20}: {value}")

if __name__ == '__main__':
    asyncio.run(main())
