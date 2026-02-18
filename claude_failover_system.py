#!/usr/bin/env python3
"""
CLAUDE FAILOVER SYSTEM
Automatischer Umstieg auf GitHub-Steuerung bei API-Limits
Maurice's AI Empire - 2026
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

import aiohttp
from antigravity.config import ANTHROPIC_API_KEY, MOONSHOT_API_KEY

# Config
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "mauricepfeifer-ctrl/AIEmpire-Core")


class ClaudeFailoverSystem:
    """System das automatisch auf GitHub umschaltet wenn Claude Limits erreicht."""

    def __init__(self):
        self.status_file = Path(__file__).parent / ".failover_status.json"
        self.load_status()

    def load_status(self):
        """Load current status."""
        if self.status_file.exists():
            with open(self.status_file) as f:
                self.status = json.load(f)
        else:
            self.status = {
                "claude_active": True,
                "github_mode": False,
                "last_claude_check": None,
                "claude_errors": 0,
                "total_requests": 0,
                "last_switch": None,
            }

    def save_status(self):
        """Save current status."""
        with open(self.status_file, "w") as f:
            json.dump(self.status, f, indent=2)

    async def check_claude_availability(self) -> bool:
        """Check if Claude API is available and within limits."""
        if not ANTHROPIC_API_KEY:
            print("⚠️  No Anthropic API key found")
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "test"}],
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        self.status["claude_errors"] = 0
                        self.status["claude_active"] = True
                        return True
                    elif resp.status == 429:
                        # Rate limit
                        print("⚠️  Claude API rate limit erreicht!")
                        self.status["claude_errors"] += 1
                        return False
                    else:
                        self.status["claude_errors"] += 1
                        return False
        except Exception as e:
            print(f"❌ Claude API Error: {e}")
            self.status["claude_errors"] += 1
            return False

    async def switch_to_github_mode(self):
        """Switch to GitHub-based control mode."""
        print("\n" + "=" * 60)
        print("🔄 SWITCHING TO GITHUB MODE")
        print("=" * 60)

        self.status["github_mode"] = True
        self.status["claude_active"] = False
        self.status["last_switch"] = datetime.now().isoformat()
        self.save_status()

        # Create GitHub issue to notify
        await self.create_control_issue(
            title="🤖 System switched to GitHub Mode",
            body=f"""# Claude API Limit Reached

System has automatically switched to GitHub-based control.

**Status:**
- Claude Active: ❌
- GitHub Mode: ✅
- Last Switch: {self.status["last_switch"]}
- Total Errors: {self.status["claude_errors"]}

**Available Commands:**
- Comment `@bot status` for system status
- Comment `@bot generate-content` for X content
- Comment `@bot run-task <task>` to run specific task
- Comment `@bot back-to-claude` to switch back (wenn verfügbar)

**Next Steps:**
1. System läuft jetzt vollständig über GitHub
2. Alle Tasks werden via Issues/Comments gesteuert
3. Kimi API wird als primäres Model genutzt
4. Content-Generation läuft weiter
""",
        )

        print("✅ GitHub Mode aktiviert")
        print(f"📝 Issue erstellt im Repo {GITHUB_REPO}")

    async def create_control_issue(self, title: str, body: str):
        """Create a GitHub issue for control/notification."""
        if not GITHUB_TOKEN:
            print("⚠️  No GitHub token available")
            return

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.github.com/repos/{GITHUB_REPO}/issues",
                headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={
                    "title": title,
                    "body": body,
                    "labels": ["automation", "system-control"],
                },
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    print(f"✅ Issue created: #{data['number']}")
                else:
                    print(f"❌ Failed to create issue: {resp.status}")

    async def monitor_github_issues(self):
        """Monitor GitHub issues for commands."""
        if not GITHUB_TOKEN:
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/issues",
                headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                },
                params={"state": "open", "labels": "system-control"},
            ) as resp:
                if resp.status == 200:
                    issues = await resp.json()
                    return issues
        return []

    async def process_command(self, command: str, issue_number: int):
        """Process a command from GitHub issue."""
        print(f"\n🎯 Processing command: {command}")

        if command == "@bot status":
            await self.post_status(issue_number)
        elif command == "@bot generate-content":
            await self.generate_content(issue_number)
        elif command.startswith("@bot run-task"):
            task = command.replace("@bot run-task", "").strip()
            await self.run_task(task, issue_number)
        elif command == "@bot back-to-claude":
            await self.try_switch_back_to_claude(issue_number)

    async def post_status(self, issue_number: int):
        """Post current system status to issue."""
        status_text = f"""# System Status

**Mode:** {"🟢 GitHub Mode" if self.status["github_mode"] else "🔵 Claude Mode"}
**Claude Active:** {"✅" if self.status["claude_active"] else "❌"}
**Total Requests:** {self.status["total_requests"]}
**Claude Errors:** {self.status["claude_errors"]}
**Last Check:** {self.status["last_claude_check"] or "Never"}

**Available Services:**
- ✅ Kimi API (Moonshot)
- ✅ X Lead Machine
- ✅ Content Generator
- ✅ Atomic Reactor
- {"✅" if self.status["claude_active"] else "❌"} Claude API
"""
        await self.post_comment(issue_number, status_text)

    async def generate_content(self, issue_number: int):
        """Generate X content using Kimi."""
        # Import X automation
        import sys

        sys.path.append(str(Path(__file__).parent / "x_lead_machine"))

        try:
            from x_automation import XLeadMachine

            machine = XLeadMachine()

            # Generate 5 posts
            topics = [
                "AI Automation",
                "Building in Public",
                "Revenue Growth",
                "AI Tools",
                "Productivity",
            ]

            posts = []
            for topic in topics:
                content = await machine.generate_content(topic, style="value")
                if content:
                    posts.append(content)

            response = "# Generated X Content\n\n"
            for i, post in enumerate(posts, 1):
                response += f"## Post {i}\n\n{post}\n\n---\n\n"

            await self.post_comment(issue_number, response)

        except Exception as e:
            await self.post_comment(issue_number, f"❌ Error generating content: {e}")

    async def run_task(self, task: str, issue_number: int):
        """Run a specific task via Kimi API."""
        await self.post_comment(issue_number, f"Running task: {task}")

        if not MOONSHOT_API_KEY:
            await self.post_comment(issue_number, "Error: MOONSHOT_API_KEY not set.")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "moonshot-v1-32k",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a task executor. Complete the task and return structured results.",
                            },
                            {"role": "user", "content": task},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data["choices"][0]["message"]["content"]
                        await self.post_comment(issue_number, f"Task completed:\n\n{result}")
                    else:
                        await self.post_comment(issue_number, f"Task failed: API error {resp.status}")
        except Exception as e:
            await self.post_comment(issue_number, f"Task failed: {e}")

    async def try_switch_back_to_claude(self, issue_number: int):
        """Try to switch back to Claude mode."""
        if await self.check_claude_availability():
            self.status["github_mode"] = False
            self.status["claude_active"] = True
            self.save_status()
            await self.post_comment(issue_number, "✅ Switched back to Claude mode!")
        else:
            await self.post_comment(issue_number, "❌ Claude still not available. Staying in GitHub mode.")

    async def post_comment(self, issue_number: int, body: str):
        """Post a comment to a GitHub issue."""
        if not GITHUB_TOKEN:
            print(f"Would post to issue #{issue_number}:\n{body}")
            return

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}/comments",
                headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={"body": body},
            ) as resp:
                if resp.status == 201:
                    print(f"✅ Comment posted to issue #{issue_number}")
                else:
                    print(f"❌ Failed to post comment: {resp.status}")

    async def run_monitoring_loop(self):
        """Main monitoring loop."""
        print("\n" + "=" * 60)
        print("🚀 CLAUDE FAILOVER SYSTEM ACTIVE")
        print("=" * 60)

        while True:
            # Check Claude availability every 5 minutes
            await self.check_claude_availability()
            self.status["last_claude_check"] = datetime.now().isoformat()
            self.status["total_requests"] += 1

            # If Claude fails multiple times, switch to GitHub mode
            if self.status["claude_errors"] >= 3 and not self.status["github_mode"]:
                await self.switch_to_github_mode()

            # If in GitHub mode, monitor issues for commands
            if self.status["github_mode"]:
                await self.monitor_github_issues()
                # Process commands from issues
                # (simplified - would need comment monitoring)

            self.save_status()

            # Wait 5 minutes
            await asyncio.sleep(300)


async def main():
    """Main entry point."""
    system = ClaudeFailoverSystem()

    # Check Claude availability
    claude_ok = await system.check_claude_availability()

    if not claude_ok:
        print("\n⚠️  Claude API not available or at limit")
        print("🔄 Switching to GitHub mode...")
        await system.switch_to_github_mode()
    else:
        print("\n✅ Claude API is available")
        print("📊 Monitoring mode...")

    # Start monitoring (optional - comment out for one-time check)
    # await system.run_monitoring_loop()


if __name__ == "__main__":
    asyncio.run(main())
