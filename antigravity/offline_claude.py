"""
Offline Claude Emulator — Local LLM Claude Alternative
=======================================================
Runs on your machine, free, using Ollama + open models.
Seamless fallback when:
  - Online Claude context limit reached
  - Network unavailable
  - API costs need reduction

Models used:
  - Qwen2.5-Coder:14b (best for code)
  - Mistral (fast, good reasoning)
  - Llama2 (good general purpose)

Behavior mirrors Claude:
  - Thinks step-by-step
  - Explains reasoning
  - Provides code with explanations
  - Handles long context (8K-32K tokens)
"""

import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from antigravity.ollama_client import OllamaClient
from antigravity.config import PROJECT_ROOT


class ClaudeRole(str, Enum):
    """Claude-like roles for different tasks."""
    ARCHITECT = "architect"      # System design, planning
    CODER = "coder"              # Code implementation
    ANALYST = "analyst"          # Data analysis, research
    REVIEWER = "reviewer"        # Code review, QA
    CONSULTANT = "consultant"    # Strategic thinking


@dataclass
class ClaudePrompt:
    """A Claude-like system prompt."""
    role: ClaudeRole
    task: str
    context: str = ""
    constraints: list = None
    output_format: str = "markdown"

    def to_system_prompt(self) -> str:
        """Convert to system prompt for local LLM."""
        constraints_text = ""
        if self.constraints:
            constraints_text = "\n\nConstraints:\n" + "\n".join(
                f"- {c}" for c in self.constraints
            )

        context_text = f"\n\nContext:\n{self.context}" if self.context else ""

        return f"""You are Claude, an AI assistant created by Anthropic.

Role: {self.role.value.upper()} - {self.task}

Your approach:
- Think step-by-step before responding
- Explain your reasoning clearly
- Provide complete, production-ready solutions
- Ask clarifying questions if needed
- Acknowledge limitations honestly
- Suggest alternatives when appropriate{constraints_text}{context_text}

Output format: {self.output_format}

Think carefully and provide high-quality analysis."""


class OfflineClaude:
    """
    Local Claude emulator using Ollama models.

    Usage:
        claude = OfflineClaude()
        response = await claude.think(
            task="Design authentication system",
            role=ClaudeRole.ARCHITECT
        )
    """

    # Model rankings by task type
    MODEL_RANKING = {
        "code": ["qwen2.5-coder:14b", "mistral", "llama2"],
        "reasoning": ["mistral", "qwen2.5-coder:14b", "llama2"],
        "analysis": ["qwen2.5-coder:14b", "mistral"],
        "creative": ["mistral", "llama2"],
        "general": ["qwen2.5-coder:14b", "mistral", "llama2"],
    }

    def __init__(self):
        self.ollama = OllamaClient()
        self.conversation_history = []
        self.context_window = 8192  # Default
        self.used_tokens = 0
        self.session_id = self._generate_session_id()
        self.model = None
        self._ensure_models()

    def _ensure_models(self) -> None:
        """Ensure at least one model is available."""
        try:
            models = self.ollama.list_models()
            if not models:
                print("❌ No models available in Ollama")
                print("   Install: ollama pull qwen2.5-coder:14b")
                return

            self.available_models = [m.get("name") for m in models]
            # Pick best available
            for preferred in self.MODEL_RANKING["code"]:
                if any(preferred in m for m in self.available_models):
                    self.model = preferred
                    break

            if not self.model:
                self.model = self.available_models[0]

            print(f"✓ Using model: {self.model}")
        except Exception as e:
            print(f"❌ Ollama error: {e}")

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return f"claude_{int(time.time())}_{os.getpid()}"

    async def think(
        self,
        task: str,
        role: ClaudeRole = ClaudeRole.CODER,
        context: str = "",
        constraints: list = None,
        task_type: str = "code",
    ) -> dict:
        """
        Ask Claude (offline version) to think about a task.

        Args:
            task: What to do
            role: ARCHITECT, CODER, ANALYST, REVIEWER, CONSULTANT
            context: Additional context
            constraints: List of constraints
            task_type: For model selection (code, reasoning, analysis, creative)

        Returns:
            {
                "thinking": "step by step reasoning",
                "response": "full response",
                "model": "which model was used",
                "tokens_used": estimate,
                "session_id": "session identifier"
            }
        """
        if not self.model:
            return {
                "error": "No Ollama models available",
                "fix": "Run: ollama pull qwen2.5-coder:14b",
            }

        try:
            # Select model based on task type
            model = self._select_model(task_type)

            # Build prompt
            prompt = ClaudePrompt(
                role=role,
                task=task,
                context=context,
                constraints=constraints,
            )

            system_prompt = prompt.to_system_prompt()

            # Get response
            print(f"\n🤔 Thinking with {model}...\n")

            response = await self.ollama.generate(
                model=model,
                prompt=task,
                system=system_prompt,
                stream=True,  # Stream for faster perceived response
            )

            # Estimate tokens (rough: ~4 chars per token)
            estimated_tokens = len(task) // 4 + len(response) // 4

            # Save to conversation history
            self.conversation_history.append({
                "timestamp": time.time(),
                "role": "user",
                "task": task,
                "response": response,
                "model": model,
                "tokens": estimated_tokens,
            })

            self.used_tokens += estimated_tokens

            return {
                "thinking": f"Used {model} to reason about: {task}",
                "response": response,
                "model": model,
                "tokens_used": estimated_tokens,
                "session_id": self.session_id,
                "total_tokens_this_session": self.used_tokens,
            }

        except Exception as e:
            return {
                "error": f"Error: {e}",
                "suggestion": "Make sure Ollama is running: ollama serve",
            }

    async def conversation(
        self,
        user_message: str,
        system_context: str = "",
    ) -> str:
        """
        Have a conversation with offline Claude.

        Maintains conversation history for context.
        """
        if not self.model:
            return "❌ No models available. Run: ollama pull qwen2.5-coder:14b"

        # Build conversation context
        messages_context = ""
        if self.conversation_history:
            messages_context = "\n\nPrevious conversation:\n"
            for msg in self.conversation_history[-3:]:  # Last 3 for context
                messages_context += f"User: {msg['task'][:100]}...\n"

        system_prompt = f"""You are Claude, an AI assistant by Anthropic.

You are helpful, harmless, and honest.
Think step-by-step through problems.
Provide clear explanations.
Suggest alternatives when appropriate.{messages_context}"""

        if system_context:
            system_prompt += f"\n\nContext:\n{system_context}"

        try:
            response = await self.ollama.generate(
                model=self.model,
                prompt=user_message,
                system=system_prompt,
            )

            # Add to history
            self.conversation_history.append({
                "timestamp": time.time(),
                "role": "user",
                "message": user_message,
                "response": response,
            })

            return response

        except Exception as e:
            return f"Error: {e}"

    def _select_model(self, task_type: str) -> str:
        """Select best model for task type."""
        models = self.MODEL_RANKING.get(task_type, self.MODEL_RANKING["general"])

        for preferred in models:
            if any(preferred in m for m in self.available_models):
                return preferred

        return self.model

    def get_status(self) -> dict:
        """Get offline Claude status."""
        return {
            "model": self.model,
            "available_models": self.available_models,
            "session_id": self.session_id,
            "tokens_used_this_session": self.used_tokens,
            "conversation_length": len(self.conversation_history),
            "status": "✓ READY" if self.model else "❌ NO MODELS",
        }

    def save_session(self) -> str:
        """Save conversation session to file."""
        session_file = (
            Path(PROJECT_ROOT)
            / "antigravity"
            / "_sessions"
            / f"{self.session_id}.json"
        )
        session_file.parent.mkdir(parents=True, exist_ok=True)

        with open(session_file, "w") as f:
            json.dump(
                {
                    "session_id": self.session_id,
                    "model": self.model,
                    "total_tokens": self.used_tokens,
                    "conversation_length": len(self.conversation_history),
                    "history": self.conversation_history,
                    "created": time.time(),
                },
                f,
                indent=2,
            )

        return str(session_file)


# ─── Async Wrapper (for use with async/await) ──────────────────────────────

class AsyncOfflineClaude(OfflineClaude):
    """Async version of OfflineClaude."""

    async def think(
        self,
        task: str,
        role: ClaudeRole = ClaudeRole.CODER,
        context: str = "",
        constraints: list = None,
        task_type: str = "code",
    ) -> dict:
        """Same as sync version but callable with await."""
        return await super().think(
            task=task,
            role=role,
            context=context,
            constraints=constraints,
            task_type=task_type,
        )


# ─── Utility Functions ──────────────────────────────────────────────────────

def get_offline_claude() -> OfflineClaude:
    """Get global offline Claude instance."""
    global _claude
    if "_claude" not in globals():
        _claude = OfflineClaude()
    return _claude


async def offline_think(
    task: str,
    role: str = "coder",
    context: str = "",
) -> dict:
    """Quick helper function."""
    claude = get_offline_claude()
    return await claude.think(
        task=task,
        role=ClaudeRole(role),
        context=context,
    )


if __name__ == "__main__":
    import asyncio

    # Test
    async def test():
        print("=== OFFLINE CLAUDE TEST ===\n")

        claude = OfflineClaude()
        print(f"Status: {claude.get_status()}\n")

        # Test 1: Architecture
        print("Test 1: Architecture")
        result = await claude.think(
            task="Design a caching system for our API",
            role=ClaudeRole.ARCHITECT,
            constraints=[
                "Must work on 3.8GB RAM system",
                "Latency < 100ms",
                "Handle 1000 requests/sec",
            ],
        )
        print(f"Response: {result['response'][:200]}...\n")

        # Test 2: Code review
        print("Test 2: Code Review")
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        result = await claude.think(
            task=f"Review this code and suggest improvements:\n{code}",
            role=ClaudeRole.REVIEWER,
        )
        print(f"Review: {result['response'][:200]}...\n")

        # Save session
        session_file = claude.save_session()
        print(f"Session saved: {session_file}")

    asyncio.run(test())
