#!/usr/bin/env python3
"""
ANTIGRAVITY CHAT - Interactive Chat Interface for Antigravity Agents
=====================================================================
Nutze die 4 Antigravity-Agents (Architect, Fixer, Coder, QA) wie einen normalen Chat.

Usage:
    python3 antigravity_chat.py                    # Start interactive chat
    python3 antigravity_chat.py --agent architect  # Start with specific agent
    python3 antigravity_chat.py --list             # List available agents

Commands in chat:
    /switch <agent>   Switch to different agent
    /list             List all available agents
    /clear            Clear conversation history
    /export           Export conversation to file
    /help             Show help
    /quit or /exit    Exit chat
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

# Import chat manager
from chat_manager import ChatManager


class AntigravityChat:
    """Interactive chat interface for Antigravity agents."""

    def __init__(self, initial_agent: str = "antigravity-coder"):
        self.manager = ChatManager()
        self.current_agent = initial_agent
        self.running = True

        # Filter only Antigravity agents
        self.agents = {
            k: v for k, v in self.manager.supported_models.items()
            if k.startswith("antigravity-")
        }

    def print_header(self):
        """Print chat header."""
        print("\n" + "=" * 70)
        print("🚀 ANTIGRAVITY CHAT - Local Specialized Coding Agents")
        print("=" * 70)
        print("\nAvailable Agents:")
        for key, info in self.agents.items():
            status = "✅" if info["available"] else "❌"
            agent_id = key.replace("antigravity-", "")
            print(f"  {status} {agent_id:12s} - {info['name']}")
            print(f"     └─ {info.get('description', 'No description')}")

        current_info = self.agents[self.current_agent]
        print(f"\n🤖 Current Agent: {current_info['name']}")
        print(f"📝 Description: {current_info.get('description', 'N/A')}")
        print("\nCommands: /switch /list /clear /export /help /quit")
        print("=" * 70 + "\n")

    def print_help(self):
        """Print help message."""
        print("\n📖 HELP - Available Commands:")
        print("-" * 50)
        print("  /switch <agent>   Switch to different agent")
        print("                    (architect, fixer, coder, qa)")
        print("  /list             List all available agents")
        print("  /clear            Clear conversation history")
        print("  /export           Export conversation to file")
        print("  /help             Show this help")
        print("  /quit or /exit    Exit chat")
        print("-" * 50 + "\n")

    def print_agents(self):
        """Print list of agents."""
        print("\n📋 Available Agents:")
        for key, info in self.agents.items():
            agent_id = key.replace("antigravity-", "")
            current = "👉" if key == self.current_agent else "  "
            print(f"{current} {agent_id:12s} - {info['name']}")
            print(f"     └─ {info.get('description', 'N/A')}")
        print()

    async def switch_agent(self, agent_name: str):
        """Switch to a different agent."""
        agent_key = f"antigravity-{agent_name}" if not agent_name.startswith("antigravity-") else agent_name

        if agent_key not in self.agents:
            print(f"\n❌ Unknown agent: {agent_name}")
            print(f"Available: {', '.join([k.replace('antigravity-', '') for k in self.agents.keys()])}\n")
            return

        self.current_agent = agent_key
        result = self.manager.switch_model(agent_key)

        if result.get("success"):
            info = self.agents[agent_key]
            print(f"\n✅ Switched to: {info['name']}")
            print(f"📝 {info.get('description', 'N/A')}\n")
        else:
            print(f"\n❌ Error switching agent: {result.get('error', 'Unknown error')}\n")

    def export_conversation(self):
        """Export conversation to file."""
        export_data = self.manager.export_conversation()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"antigravity_chat_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(export_data)

        print(f"\n✅ Conversation exported to: {filename}\n")

    async def handle_command(self, command: str) -> bool:
        """Handle special commands. Returns True if command was handled."""
        parts = command.strip().split()
        cmd = parts[0].lower()

        if cmd in ["/quit", "/exit"]:
            self.running = False
            print("\n👋 Bye! Chat session ended.\n")
            return True

        elif cmd == "/help":
            self.print_help()
            return True

        elif cmd == "/list":
            self.print_agents()
            return True

        elif cmd == "/clear":
            self.manager.clear_history()
            print("\n✅ Conversation history cleared.\n")
            return True

        elif cmd == "/export":
            self.export_conversation()
            return True

        elif cmd == "/switch":
            if len(parts) < 2:
                print("\n❌ Usage: /switch <agent>\n")
            else:
                await self.switch_agent(parts[1])
            return True

        return False

    async def chat_loop(self):
        """Main chat loop."""
        self.print_header()

        while self.running:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                    continue

                # Send to agent
                current_info = self.agents[self.current_agent]
                agent_name = current_info["name"].replace(" (Local)", "")

                print(f"\n{agent_name}: ", end="", flush=True)

                response = await self.manager.ask_question(
                    user_input,
                    model=self.current_agent,
                    use_history=True
                )

                if response.get("success"):
                    answer = response.get("answer", "No response")
                    print(answer)

                    # Show branch info if available
                    if response.get("branch"):
                        print(f"\n📁 Branch: {response['branch']}", end="")

                    print()  # Newline after response
                else:
                    error = response.get("error", "Unknown error")
                    print(f"❌ Error: {error}\n")

            except KeyboardInterrupt:
                self.running = False
                print("\n\n👋 Chat interrupted. Bye!\n")
                break

            except EOFError:
                self.running = False
                print("\n\n👋 Chat ended. Bye!\n")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                continue


async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Antigravity Chat - Interactive interface for specialized coding agents"
    )
    parser.add_argument(
        "--agent",
        "-a",
        default="coder",
        choices=["architect", "fixer", "coder", "qa"],
        help="Initial agent to use (default: coder)"
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available agents and exit"
    )

    args = parser.parse_args()

    # List agents and exit
    if args.list:
        chat = AntigravityChat()
        chat.print_agents()
        return

    # Start chat
    initial_agent = f"antigravity-{args.agent}"
    chat = AntigravityChat(initial_agent=initial_agent)
    await chat.chat_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bye!\n")
        sys.exit(0)
