"""
SkyBot Agent — Claude-powered AI Agent with Tool Use
=====================================================
Core agent loop:
  1. User sends message
  2. Claude reasons + decides which tools to use
  3. Tools execute and return results
  4. Claude processes results and responds (or calls more tools)
  5. Final response sent back to user

Supports both Anthropic Claude API and local Ollama fallback.
"""

import json
import logging
import time
from typing import Optional

from skybot.config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    MAX_TOKENS,
    MAX_TOOL_ROUNDS,
    OLLAMA_URL,
    OLLAMA_MODEL,
    MOONSHOT_API_KEY,
)

log = logging.getLogger("skybot.agent")

# System prompt for the agent
SYSTEM_PROMPT = """You are SkyBot, an advanced AI agent running on Maurice Pfeifer's computer.
You are part of the AIEmpire system — an automated business empire combining BMA (fire alarm systems) expertise with AI automation.

You have access to tools that let you:
- Search the web and fetch URLs
- Execute Python and Bash code
- Read, write, and manage files in your workspace
- Search GitHub for repositories, code, and trends
- Build websites (HTML/CSS/JS)

RULES:
- Always explain what you're doing before using a tool
- Be concise but thorough in your responses
- If a task requires multiple steps, plan first, then execute
- Never execute dangerous commands (rm -rf /, system modifications, etc.)
- Respond in the same language the user writes in (German or English)
- For code, always show the result after execution
- If unsure, ask for clarification

CONTEXT:
- Owner: Maurice Pfeifer, 37, Elektrotechnikmeister, 16 years BMA expertise
- Goal: Build automated revenue streams using AI
- Revenue channels: Gumroad products, Fiverr services, BMA consulting, AI community
- Tech stack: Ollama (local AI), Kimi (bulk), Claude (critical), Python, asyncio
"""


class SkyBotAgent:
    """The core agent that orchestrates Claude + Tools."""

    def __init__(self):
        self.conversation_history: list[dict] = []
        self._anthropic_client = None
        self._tools = None
        self._tool_definitions = None
        self._tools_by_name = None

    def _get_tools(self):
        """Lazy-load tools to avoid import issues."""
        if self._tools is None:
            from skybot.tools import TOOL_DEFINITIONS, TOOLS_BY_NAME
            self._tool_definitions = TOOL_DEFINITIONS
            self._tools_by_name = TOOLS_BY_NAME
        return self._tool_definitions, self._tools_by_name

    def _get_client(self):
        """Lazy-init Anthropic client."""
        if self._anthropic_client is None:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            except ImportError:
                log.error("anthropic package not installed. Run: pip3 install anthropic")
                return None
            except Exception as e:
                log.error(f"Failed to init Anthropic client: {e}")
                return None
        return self._anthropic_client

    async def chat(self, user_message: str) -> str:
        """
        Main entry point: send a message and get a response.
        Handles the full tool-use loop.
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Try Claude first, fallback to Ollama
        if ANTHROPIC_API_KEY:
            response = await self._chat_claude()
        elif MOONSHOT_API_KEY:
            response = await self._chat_kimi(user_message)
        else:
            response = await self._chat_ollama(user_message)

        return response

    async def _chat_claude(self) -> str:
        """Full Claude conversation with tool use loop."""
        client = self._get_client()
        if not client:
            return "ERROR: Anthropic client not available. Check ANTHROPIC_API_KEY."

        tool_defs, tools_by_name = self._get_tools()
        rounds = 0

        while rounds < MAX_TOOL_ROUNDS:
            rounds += 1
            log.info(f"Claude API call (round {rounds}/{MAX_TOOL_ROUNDS})")

            try:
                response = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    tools=tool_defs,
                    messages=self.conversation_history,
                )
            except Exception as e:
                error_msg = f"Claude API error: {e}"
                log.error(error_msg)
                return error_msg

            # Process response
            assistant_content = response.content
            stop_reason = response.stop_reason

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_content,
            })

            # If no tool use, extract text and return
            if stop_reason == "end_turn" or stop_reason != "tool_use":
                text_parts = [
                    block.text for block in assistant_content
                    if hasattr(block, "text")
                ]
                final_response = "\n".join(text_parts) if text_parts else "(No text response)"

                # Log usage
                usage = response.usage
                log.info(
                    f"Claude done. Input: {usage.input_tokens}, "
                    f"Output: {usage.output_tokens}, Rounds: {rounds}"
                )

                return final_response

            # Tool use — execute all tool calls
            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                log.info(f"Tool call: {tool_name}({json.dumps(tool_input, ensure_ascii=False)[:200]})")

                tool = tools_by_name.get(tool_name)
                if tool is None:
                    result = f"Unknown tool: {tool_name}"
                else:
                    try:
                        result = await tool.execute(**tool_input)
                    except Exception as e:
                        result = f"Tool execution error: {e}"
                        log.error(f"Tool {tool_name} failed: {e}")

                log.info(f"Tool result: {result[:200]}...")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result,
                })

            # Add tool results to history
            self.conversation_history.append({
                "role": "user",
                "content": tool_results,
            })

        return "Maximum tool rounds reached. The task may be incomplete."

    async def _chat_ollama(self, message: str) -> str:
        """Fallback: Ollama local model (no tool use, just chat)."""
        import aiohttp

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            "stream": False,
        }

        try:
            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{OLLAMA_URL}/api/chat", json=payload) as r:
                    if r.status == 200:
                        data = await r.json()
                        answer = data.get("message", {}).get("content", "No response")
                        return f"[Ollama/{OLLAMA_MODEL}]\n\n{answer}"
                    else:
                        return f"Ollama error: HTTP {r.status}"
        except Exception as e:
            return f"Ollama not available: {e}\n\nSet ANTHROPIC_API_KEY in .env for full agent mode."

    async def _chat_kimi(self, message: str) -> str:
        """Fallback: Kimi/Moonshot cloud (no tool use, just chat)."""
        import aiohttp

        headers = {
            "Authorization": f"Bearer {MOONSHOT_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "moonshot-v1-8k",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        choices = data.get("choices", [])
                        if not choices:
                            return "Kimi API error: empty response"
                        answer = choices[0].get("message", {}).get("content")
                        if not answer:
                            return "Kimi API error: no content in response"
                        return f"[Kimi Cloud]\n\n{answer}"
                    else:
                        return f"Kimi API error: HTTP {r.status}"
        except Exception as e:
            return f"Kimi not available: {e}"

    def reset(self):
        """Clear conversation history."""
        self.conversation_history.clear()

    def get_stats(self) -> dict:
        """Return conversation stats."""
        return {
            "messages": len(self.conversation_history),
            "model": CLAUDE_MODEL if ANTHROPIC_API_KEY else (
                "Kimi" if MOONSHOT_API_KEY else f"Ollama/{OLLAMA_MODEL}"
            ),
            "has_anthropic_key": bool(ANTHROPIC_API_KEY),
            "has_moonshot_key": bool(MOONSHOT_API_KEY),
            "max_tool_rounds": MAX_TOOL_ROUNDS,
        }
