"""
Ant Worker - Autonomous Task Agent
====================================
Each worker ant:
  1. Registers with colony
  2. Polls task board (follows pheromone trails)
  3. Claims task atomically
  4. Executes via LiteLLM
  5. Reports result back to colony
  6. Sends heartbeats
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

from .colony import Colony
from .config import (
    DEFAULT_WORKER_MODEL,
    HEARTBEAT_INTERVAL,
    LITELLM_BASE_URL,
)
from .protocol import (
    AntTask,
    TaskStatus,
    WorkerInfo,
    WorkerStatus,
)

log = logging.getLogger("ant.worker")


class AntWorker:
    """Autonomous worker ant that picks up and executes tasks."""

    def __init__(
        self,
        name: str = "",
        skills: list[str] | None = None,
        model: str = DEFAULT_WORKER_MODEL,
        colony: Colony | None = None,
    ):
        self.info = WorkerInfo(
            worker_id=f"ant-{str(uuid.uuid4())[:8]}",
            name=name or f"worker-{str(uuid.uuid4())[:4]}",
            skills=skills or ["general"],
            model=model,
        )
        self.colony = colony or Colony()
        self._running = False
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """Start the worker ant lifecycle."""
        if aiohttp is None:
            raise ImportError("aiohttp required: pip install aiohttp")

        await self.colony.connect()
        registered = await self.colony.register_worker(self.info)
        if not registered:
            log.error(f"Worker {self.info.worker_id} rejected by colony (full)")
            return

        self._running = True
        self._session = aiohttp.ClientSession()
        log.info(f"Worker {self.info.worker_id} ({self.info.name}) started, skills={self.info.skills}")

        # Run main loop and heartbeat concurrently
        await asyncio.gather(
            self._work_loop(),
            self._heartbeat_loop(),
        )

    async def stop(self):
        """Stop the worker gracefully."""
        self._running = False
        if self._session:
            await self._session.close()
        await self.colony.close()
        log.info(f"Worker {self.info.worker_id} stopped")

    async def _work_loop(self):
        """Main work loop: discover -> claim -> execute -> report."""
        while self._running:
            try:
                task = await self._discover_task()
                if task:
                    await self._execute_task(task)
                else:
                    # No work available, wait before polling again
                    await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Worker {self.info.worker_id} error: {e}")
                await asyncio.sleep(10)

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to colony."""
        while self._running:
            try:
                await self.colony.heartbeat(self.info.worker_id, self.info.load)
            except Exception as e:
                log.warning(f"Heartbeat failed: {e}")
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def _discover_task(self) -> Optional[AntTask]:
        """Find and claim the best task for this worker."""
        tasks = await self.colony.get_available_tasks(20)
        if not tasks:
            return None

        # Score tasks by: priority * pheromone * skill_match
        scored = []
        for task in tasks:
            score = task.priority * task.pheromone_strength
            # Skill matching bonus
            if task.required_skills:
                matches = len(set(task.required_skills) & set(self.info.skills))
                total = len(task.required_skills)
                skill_score = matches / total if total > 0 else 0.5
                score *= (0.5 + skill_score)
            # Age bonus (older tasks get priority)
            age_bonus = min(task.age_seconds / 300, 2.0)
            score += age_bonus
            scored.append((score, task))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Try to claim the best matching task
        for _, task in scored:
            claimed = await self.colony.claim_task(task.task_id, self.info.worker_id)
            if claimed:
                return claimed
        return None

    async def _execute_task(self, task: AntTask):
        """Execute a claimed task via LiteLLM."""
        self.info.status = WorkerStatus.BUSY
        self.info.current_task = task.task_id
        self.info.load = 0.8

        log.info(f"Worker {self.info.worker_id} executing task {task.task_id}: {task.title}")

        try:
            # Build prompt from task
            prompt = self._build_prompt(task)

            # Call LiteLLM
            result = await self._call_llm(prompt, task)

            # Report success
            await self.colony.complete_task(task.task_id, self.info.worker_id, result)
            self.info.tasks_completed += 1
            log.info(f"Task {task.task_id} completed successfully")

        except Exception as e:
            error_msg = str(e)
            log.error(f"Task {task.task_id} failed: {error_msg}")
            await self.colony.fail_task(task.task_id, self.info.worker_id, error_msg)
            self.info.tasks_failed += 1

        finally:
            self.info.status = WorkerStatus.IDLE
            self.info.current_task = ""
            self.info.load = 0.0

    def _build_prompt(self, task: AntTask) -> str:
        """Build LLM prompt from task."""
        parts = [
            f"# Task: {task.title}",
            f"\n## Description\n{task.description}",
            f"\n## Type: {task.task_type}",
            f"## Priority: {task.priority}/10",
        ]
        if task.payload:
            parts.append(f"\n## Additional Context\n```json\n{json.dumps(task.payload, indent=2)}\n```")
        parts.append("\n## Instructions")
        parts.append("Execute this task and return a structured JSON result with:")
        parts.append('- "output": the main result/content')
        parts.append('- "summary": 1-2 sentence summary')
        parts.append('- "next_steps": suggested follow-up actions (list)')
        parts.append('\nReturn ONLY valid JSON.')
        return "\n".join(parts)

    async def _call_llm(self, prompt: str, task: AntTask) -> dict:
        """Call LiteLLM API for task execution."""
        model = task.payload.get("model", self.info.model)
        url = f"{LITELLM_BASE_URL}/chat/completions"

        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are an AI worker ant in colony '{self.colony.colony_id}'. Execute tasks efficiently and return structured JSON results."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        async with self._session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"LLM call failed ({resp.status}): {text}")
            data = await resp.json()

        content = data["choices"][0]["message"]["content"]

        # Try to parse as JSON
        try:
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return {"output": content, "summary": content[:200], "next_steps": []}


async def run_worker(
    name: str = "",
    skills: list[str] | None = None,
    model: str = DEFAULT_WORKER_MODEL,
    count: int = 1,
):
    """Launch one or more worker ants."""
    if count == 1:
        worker = AntWorker(name=name, skills=skills, model=model)
        await worker.start()
    else:
        workers = [
            AntWorker(name=f"{name or 'worker'}-{i}", skills=skills, model=model)
            for i in range(count)
        ]
        await asyncio.gather(*(w.start() for w in workers))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start Ant Worker(s)")
    parser.add_argument("--name", default="", help="Worker name")
    parser.add_argument("--skills", nargs="+", default=["general"], help="Worker skills")
    parser.add_argument("--model", default=DEFAULT_WORKER_MODEL, help="LLM model")
    parser.add_argument("--count", type=int, default=1, help="Number of workers to spawn")
    args = parser.parse_args()

    asyncio.run(run_worker(args.name, args.skills, args.model, args.count))
