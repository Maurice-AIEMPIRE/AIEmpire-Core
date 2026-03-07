#!/usr/bin/env python3
"""
CHAT MANAGER - Chat Upload & Multi-Model Support
Ermöglicht Chat-Upload und Fragen mit allen verfügbaren Modellen
Maurice's AI Empire - 2026
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from antigravity.config import (
    ANTHROPIC_API_KEY,
    MOONSHOT_API_KEY,
    OLLAMA_BASE_URL,
)

# Storage paths
CHAT_HISTORY_DIR = Path(__file__).parent / "chat_history"
CHAT_HISTORY_DIR.mkdir(exist_ok=True)


class ChatManager:
    """Manager für Chat-Upload und Multi-Model Support."""

    def __init__(self):
        self.supported_models = {
            "claude": {
                "name": "Claude Haiku 4.5",
                "api": "anthropic",
                "model_id": "claude-haiku-4-5-20251001",
                "available": bool(ANTHROPIC_API_KEY),
            },
            "claude-sonnet": {
                "name": "Claude Sonnet 4.5",
                "api": "anthropic",
                "model_id": "claude-sonnet-4-5-20250929",
                "available": bool(ANTHROPIC_API_KEY),
            },
            "claude-opus": {
                "name": "Claude Opus 4.5",
                "api": "anthropic",
                "model_id": "claude-opus-4-5-20251101",
                "available": bool(ANTHROPIC_API_KEY),
            },
            "kimi": {
                "name": "Kimi (Moonshot)",
                "api": "moonshot",
                "model_id": "moonshot-v1-8k",
                "available": bool(MOONSHOT_API_KEY),
            },
            "ollama-qwen": {
                "name": "Qwen 2.5 Coder (Local)",
                "api": "ollama",
                "model_id": "qwen2.5-coder:7b",
                "available": True,  # Assume Ollama is available locally
            },
            "ollama-mistral": {
                "name": "Mistral (Local)",
                "api": "ollama",
                "model_id": "mistral:7b",
                "available": True,
            },
        }
        self.current_model = "kimi"  # Default to Kimi (cheapest)
        self.conversation_history = []

    async def upload_chat(self, chat_data: str, format: str = "json") -> Dict:
        """
        Upload chat history from various formats.

        Args:
            chat_data: Chat content as string
            format: Format type - 'json', 'text', 'markdown'

        Returns:
            Dict with upload status and chat_id
        """
        try:
            if format == "json":
                messages = json.loads(chat_data)
            elif format == "text":
                messages = self._parse_text_chat(chat_data)
            elif format == "markdown":
                messages = self._parse_markdown_chat(chat_data)
            else:
                return {"error": f"Unsupported format: {format}"}

            # Save to history
            chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = CHAT_HISTORY_DIR / f"chat_{chat_id}.json"

            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "chat_id": chat_id,
                        "uploaded_at": datetime.now().isoformat(),
                        "format": format,
                        "messages": messages,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            self.conversation_history = messages

            return {
                "success": True,
                "chat_id": chat_id,
                "message_count": len(messages),
                "file": str(history_file),
            }

        except Exception as e:
            return {"error": str(e)}

    def _parse_text_chat(self, text: str) -> List[Dict]:
        """Parse plain text chat format."""
        messages = []
        lines = text.strip().split("\n")

        current_role = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect role changes
            if line.lower().startswith(("user:", "assistant:", "system:")):
                # Save previous message
                if current_role and current_content:
                    messages.append({"role": current_role, "content": "\n".join(current_content)})
                    current_content = []

                # Parse new role
                parts = line.split(":", 1)
                current_role = parts[0].lower()
                if len(parts) > 1:
                    current_content = [parts[1].strip()]
            else:
                current_content.append(line)

        # Save last message
        if current_role and current_content:
            messages.append({"role": current_role, "content": "\n".join(current_content)})

        return messages

    def _parse_markdown_chat(self, markdown: str) -> List[Dict]:
        """Parse markdown chat format."""
        messages = []
        sections = markdown.split("\n## ")

        for section in sections:
            section = section.strip()
            if not section:
                continue

            lines = section.split("\n", 1)
            header = lines[0].replace("##", "").strip().lower()
            content = lines[1].strip() if len(lines) > 1 else ""

            role = "user"
            if "assistant" in header or "ai" in header:
                role = "assistant"
            elif "system" in header:
                role = "system"

            if content:
                messages.append({"role": role, "content": content})

        return messages

    async def ask_question(self, question: str, model: Optional[str] = None, use_history: bool = True) -> Dict:
        """
        Ask a question using the specified model.

        Args:
            question: The question to ask
            model: Model to use (default: current_model)
            use_history: Whether to include conversation history

        Returns:
            Dict with answer and metadata
        """
        if model is None:
            model = self.current_model

        if model not in self.supported_models:
            return {"error": f"Unknown model: {model}"}

        model_config = self.supported_models[model]

        if not model_config["available"]:
            return {"error": f"Model {model} is not available (missing API key)"}

        # Prepare messages
        messages = []
        if use_history and self.conversation_history:
            messages.extend(self.conversation_history[-10:])  # Last 10 messages

        messages.append({"role": "user", "content": question})

        # Route to appropriate API
        try:
            if model_config["api"] == "anthropic":
                response = await self._ask_anthropic(model_config["model_id"], messages)
            elif model_config["api"] == "moonshot":
                response = await self._ask_moonshot(model_config["model_id"], messages)
            elif model_config["api"] == "ollama":
                response = await self._ask_ollama(model_config["model_id"], messages)
            else:
                return {"error": f"Unknown API: {model_config['api']}"}

            # Add to history
            if response.get("success"):
                self.conversation_history.append({"role": "user", "content": question})
                self.conversation_history.append({"role": "assistant", "content": response["answer"]})

            return response

        except Exception as e:
            return {"error": str(e)}

    async def _ask_anthropic(self, model_id: str, messages: List[Dict]) -> Dict:
        """Ask Claude via Anthropic API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }

                payload = {"model": model_id, "max_tokens": 4096, "messages": messages}

                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "answer": data["content"][0]["text"],
                            "model": model_id,
                            "usage": data.get("usage", {}),
                        }
                    else:
                        error_text = await resp.text()
                        return {"error": f"Anthropic API error: {error_text}"}

        except Exception as e:
            return {"error": f"Anthropic request failed: {e}"}

    async def _ask_moonshot(self, model_id: str, messages: List[Dict]) -> Dict:
        """Ask Kimi via Moonshot API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                    "Content-Type": "application/json",
                }

                payload = {"model": model_id, "messages": messages, "temperature": 0.7}

                async with session.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "answer": data["choices"][0]["message"]["content"],
                            "model": model_id,
                            "usage": data.get("usage", {}),
                        }
                    else:
                        error_text = await resp.text()
                        return {"error": f"Moonshot API error: {error_text}"}

        except Exception as e:
            return {"error": f"Moonshot request failed: {e}"}

    async def _ask_ollama(self, model_id: str, messages: List[Dict]) -> Dict:
        """Ask Ollama (local models)."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"model": model_id, "messages": messages, "stream": False}

                async with session.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "answer": data["message"]["content"],
                            "model": model_id,
                            "local": True,
                        }
                    else:
                        error_text = await resp.text()
                        return {"error": f"Ollama error: {error_text}"}

        except Exception as e:
            return {"error": f"Ollama request failed: {e}. Is Ollama running on {OLLAMA_BASE_URL}?"}

    def switch_model(self, model_name: str) -> Dict:
        """Switch to a different model."""
        if model_name not in self.supported_models:
            return {
                "error": f"Unknown model: {model_name}",
                "available_models": list(self.supported_models.keys()),
            }

        if not self.supported_models[model_name]["available"]:
            return {
                "error": f"Model {model_name} is not available",
                "reason": "Missing API key or service not running",
            }

        old_model = self.current_model
        self.current_model = model_name

        return {
            "success": True,
            "previous_model": old_model,
            "current_model": model_name,
            "model_info": self.supported_models[model_name],
        }

    def list_models(self) -> Dict:
        """List all available models."""
        return {"current_model": self.current_model, "models": self.supported_models}

    def export_conversation(self) -> str:
        """Export current conversation as JSON."""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "model": self.current_model,
            "messages": self.conversation_history,
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_history_summary(self) -> Dict:
        """Get summary of conversation history."""
        return {
            "message_count": len(self.conversation_history),
            "user_messages": sum(1 for m in self.conversation_history if m["role"] == "user"),
            "assistant_messages": sum(1 for m in self.conversation_history if m["role"] == "assistant"),
            "current_model": self.current_model,
        }


async def main():
    """Test the chat manager."""
    print("=" * 60)
    print("CHAT MANAGER - Test")
    print("=" * 60)
    print()

    manager = ChatManager()

    # List available models
    print("### Available Models")
    models_info = manager.list_models()
    print(f"Current model: {models_info['current_model']}")
    print("\nAll models:")
    for name, info in models_info["models"].items():
        status = "✅" if info["available"] else "❌"
        print(f"  {status} {name}: {info['name']}")
    print()

    # Test upload
    print("### Testing Chat Upload")
    test_chat = """User: Hello, how are you?
Assistant: I'm doing well, thank you! How can I help you today?
User: I want to learn about AI automation.
Assistant: Great! AI automation is a powerful way to streamline tasks."""

    result = await manager.upload_chat(test_chat, format="text")
    print(f"Upload result: {json.dumps(result, indent=2)}")
    print()

    # Test question
    print("### Testing Question")
    answer = await manager.ask_question("What is AI automation?", use_history=True)
    print(f"Answer: {json.dumps(answer, indent=2)}")
    print()

    # Test model switch
    print("### Testing Model Switch")
    switch_result = manager.switch_model("ollama-qwen")
    print(f"Switch result: {json.dumps(switch_result, indent=2)}")
    print()

    # Export conversation
    print("### Exporting Conversation")
    exported = manager.export_conversation()
    print(f"Exported conversation length: {len(exported)} chars")


if __name__ == "__main__":
    asyncio.run(main())
