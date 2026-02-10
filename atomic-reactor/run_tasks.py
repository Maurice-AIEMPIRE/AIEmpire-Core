#!/usr/bin/env python3
"""
ATOMIC REACTOR - Task Runner
Führt alle Tasks in /tasks/ aus
"""

import asyncio
import aiohttp
import yaml
import json
import os
from pathlib import Path
from datetime import datetime

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "sk-e57Q5aDfcpXpHkYfgeWCU3xjuqf2ZPoYxhuRH0kEZXGBeoMF")
TASKS_DIR = Path(__file__).parent / "tasks"
REPORTS_DIR = Path(__file__).parent / "reports"

async def execute_task(task: dict) -> dict:
    """Execute a single task with Kimi."""
    prompt = task.get("prompts", [""])[0] if task.get("prompts") else task.get("objective", "")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.moonshot.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshot-v1-32k",  # Bigger context for complex tasks
                "messages": [
                    {"role": "system", "content": "You are a business analyst. Return structured JSON responses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return {
                    "task_id": task.get("id"),
                    "title": task.get("title"),
                    "status": "success",
                    "result": content,
                    "tokens": tokens,
                    "cost_usd": (tokens / 1000) * 0.001
                }
            else:
                return {
                    "task_id": task.get("id"),
                    "status": "error",
                    "error": f"HTTP {resp.status}"
                }

async def run_all_tasks():
    """Load and run all tasks from /tasks/."""
    print("=" * 60)
    print("ATOMIC REACTOR - Task Runner")
    print("=" * 60)
    print()

    REPORTS_DIR.mkdir(exist_ok=True)

    # Load all task files
    task_files = list(TASKS_DIR.glob("*.yaml"))
    print(f"Found {len(task_files)} tasks")
    print()

    results = []
    total_tokens = 0
    total_cost = 0

    for task_file in sorted(task_files):
        print(f"📋 Loading: {task_file.name}")

        with open(task_file) as f:
            task = yaml.safe_load(f)

        print(f"   Title: {task.get('title')}")
        print(f"   Type: {task.get('type')}")
        print("   Executing...")

        result = await execute_task(task)

        if result["status"] == "success":
            print(f"   ✅ Success ({result['tokens']} tokens, ${result['cost_usd']:.4f})")
            total_tokens += result["tokens"]
            total_cost += result["cost_usd"]

            # Save report
            report_file = REPORTS_DIR / f"{task.get('id')}_report.md"
            with open(report_file, "w") as f:
                f.write(f"# {task.get('title')}\n\n")
                f.write(f"**Task ID:** {task.get('id')}\n")
                f.write(f"**Type:** {task.get('type')}\n")
                f.write(f"**Executed:** {datetime.now().isoformat()}\n")
                f.write(f"**Tokens:** {result['tokens']}\n")
                f.write(f"**Cost:** ${result['cost_usd']:.4f}\n\n")
                f.write("## Result\n\n")
                f.write("```json\n")
                f.write(result["result"])
                f.write("\n```\n")

            print(f"   📝 Report: {report_file.name}")
        else:
            print(f"   ❌ Error: {result.get('error')}")

        results.append(result)
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tasks Executed: {len(results)}")
    print(f"Successful:     {sum(1 for r in results if r['status'] == 'success')}")
    print(f"Failed:         {sum(1 for r in results if r['status'] == 'error')}")
    print(f"Total Tokens:   {total_tokens:,}")
    print(f"Total Cost:     ${total_cost:.4f}")
    print()

    # Save summary
    summary_file = REPORTS_DIR / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, "w") as f:
        json.dump({
            "executed_at": datetime.now().isoformat(),
            "tasks": len(results),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "results": results
        }, f, indent=2)

    print(f"Summary saved: {summary_file}")
    return results

if __name__ == "__main__":
    asyncio.run(run_all_tasks())
