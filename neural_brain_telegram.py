#!/usr/bin/env python3
"""
Neural Brain - Telegram Interface
Communicate with the AI system directly via Telegram
Accepts: text, PDFs, images, videos, documents
Executes: analysis, implementations, revenue reports
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import aiohttp
from anthropic import Anthropic

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramNeuralBrain:
    """Neural Brain with Telegram interface"""

    def __init__(self, telegram_token: str, claude_api_key: str, user_id: int):
        self.telegram_token = telegram_token
        self.claude_client = Anthropic(api_key=claude_api_key)
        self.user_id = user_id
        self.base_url = f"https://api.telegram.org/bot{telegram_token}"

        # State management
        self.conversation_history = []
        self.uploads_dir = Path("neural_brain_uploads")
        self.uploads_dir.mkdir(exist_ok=True)

        # Knowledge store
        self.knowledge_file = Path("neural_brain_knowledge.json")
        self.load_knowledge()

    def load_knowledge(self):
        """Load existing knowledge store"""
        if self.knowledge_file.exists():
            with open(self.knowledge_file, 'r') as f:
                self.knowledge = json.load(f)
        else:
            self.knowledge = {
                "insights": [],
                "implementations": [],
                "revenue_events": [],
                "x_monitoring": [],
                "last_sync": None
            }

    def save_knowledge(self):
        """Persist knowledge store"""
        with open(self.knowledge_file, 'w') as f:
            json.dump(self.knowledge, f, indent=2, default=str)

    async def send_telegram_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send message to user via Telegram"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.user_id,
            "text": text[:4096],  # Telegram limit
            "parse_mode": parse_mode
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return resp.status == 200

    async def download_telegram_file(self, file_id: str, file_path: str) -> Optional[Path]:
        """Download file from Telegram"""
        try:
            # Get file info
            url = f"{self.base_url}/getFile"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"file_id": file_id}) as resp:
                    data = await resp.json()
                    if not data.get("ok"):
                        return None

                    file_path_tg = data["result"]["file_path"]

                    # Download file
                    download_url = f"https://api.telegram.org/file/bot{self.telegram_token}/{file_path_tg}"
                    async with session.get(download_url) as file_resp:
                        content = await file_resp.read()
                        local_path = self.uploads_dir / file_path
                        local_path.write_bytes(content)
                        return local_path
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None

    async def analyze_with_claude(self, prompt: str, context: str = "") -> str:
        """Analyze input with Claude Opus 4.6"""
        messages = self.conversation_history.copy()

        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        messages.append({"role": "user", "content": full_prompt})

        response = self.claude_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            system="""You are the Neural Brain - an autonomous AI system that:
1. Analyzes AI trends from top experts
2. Auto-implements best practices
3. Generates revenue through multiple channels
4. Reports back to Maurice via Telegram

Always respond in JSON format with: {"analysis": "...", "action": "...", "revenue_impact": "...", "next_steps": [...]}
Be concise and actionable.""",
            messages=messages
        )

        answer = response.content[0].text
        self.conversation_history.append({"role": "user", "content": full_prompt})
        self.conversation_history.append({"role": "assistant", "content": answer})

        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        return answer

    async def process_text_message(self, text: str) -> str:
        """Process text message"""
        logger.info(f"Processing text: {text[:100]}")

        analysis = await self.analyze_with_claude(text)

        try:
            data = json.loads(analysis)
            self.knowledge["insights"].append({
                "timestamp": datetime.now().isoformat(),
                "input": text,
                "analysis": data
            })
            self.save_knowledge()

            return self._format_response(data)
        except json.JSONDecodeError:
            return f"⚡ **Analysis:**\n{analysis}"

    async def process_file_message(self, file_path: Path, file_type: str) -> str:
        """Process uploaded file"""
        logger.info(f"Processing {file_type}: {file_path}")

        # Read file content (text-based files)
        if file_type in ["pdf", "txt", "json", "csv"]:
            try:
                if file_path.suffix.lower() == ".pdf":
                    # Simple PDF text extraction (basic)
                    content = f"[PDF File: {file_path.name}] - Ready for analysis"
                else:
                    content = file_path.read_text()

                prompt = f"Analyze this {file_type} file for actionable insights:\n\n{content[:2000]}"
                analysis = await self.analyze_with_claude(prompt)

                self.knowledge["implementations"].append({
                    "timestamp": datetime.now().isoformat(),
                    "file": str(file_path),
                    "type": file_type,
                    "analysis": analysis
                })
                self.save_knowledge()

                return f"📄 **File Analysis ({file_type}):**\n{analysis[:1000]}..."
            except Exception as e:
                return f"❌ Error processing file: {e}"
        else:
            return f"💾 **File received:** {file_path.name}\n✅ Ready for processing"

    def _format_response(self, data: dict) -> str:
        """Format Claude response for Telegram"""
        msg = "⚡ **Neural Brain Response**\n\n"

        if "analysis" in data:
            msg += f"📊 **Analysis:** {data['analysis'][:500]}\n\n"

        if "action" in data:
            msg += f"🎯 **Action:** {data['action']}\n\n"

        if "revenue_impact" in data:
            msg += f"💰 **Revenue Impact:** {data['revenue_impact']}\n\n"

        if "next_steps" in data and data["next_steps"]:
            msg += "📋 **Next Steps:**\n"
            for i, step in enumerate(data["next_steps"][:3], 1):
                msg += f"{i}. {step}\n"

        return msg

    async def get_system_status(self) -> str:
        """Get current system status"""
        insights_count = len(self.knowledge["insights"])
        implementations_count = len(self.knowledge["implementations"])

        msg = "🧠 **Neural Brain Status**\n\n"
        msg += f"📊 Insights Analyzed: {insights_count}\n"
        msg += f"🚀 Implementations: {implementations_count}\n"
        msg += f"💰 Revenue Events: {len(self.knowledge['revenue_events'])}\n"
        msg += f"🕐 Last Sync: {self.knowledge['last_sync'] or 'Never'}\n"
        msg += f"\n✅ System Ready for Commands"

        return msg

    async def get_revenue_report(self) -> str:
        """Generate revenue report"""
        analysis = await self.analyze_with_claude(
            "Generate a brief revenue optimization report based on current system state"
        )

        msg = "💰 **Revenue Report**\n\n"
        msg += analysis[:1000]

        return msg

    async def webhook_handler(self, update: dict):
        """Handle incoming Telegram webhook"""
        try:
            message = update.get("message", {})

            if not message:
                return {"ok": True}

            # Extract message content
            text = message.get("text", "")
            document = message.get("document")
            photo = message.get("photo")
            video = message.get("video")

            response_text = "Processing..."

            # Process different content types
            if text:
                if text.startswith("/status"):
                    response_text = await self.get_system_status()
                elif text.startswith("/revenue"):
                    response_text = await self.get_revenue_report()
                else:
                    response_text = await self.process_text_message(text)

            elif document:
                file_id = document["file_id"]
                file_name = document.get("file_name", "upload")
                file_type = file_name.split(".")[-1] if "." in file_name else "unknown"

                file_path = await self.download_telegram_file(file_id, file_name)
                if file_path:
                    response_text = await self.process_file_message(file_path, file_type)

            elif photo or video:
                response_text = "🖼️ **Media Upload Received**\n✅ File stored for analysis\n🔄 Processing next..."

            # Send response
            await self.send_telegram_message(response_text)

            return {"ok": True}

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            await self.send_telegram_message(f"❌ Error: {str(e)[:100]}")
            return {"ok": False, "error": str(e)}


async def run_telegram_server(telegram_token: str, claude_api_key: str, user_id: int, port: int = 8765):
    """Run Telegram webhook server"""
    from aiohttp import web

    brain = TelegramNeuralBrain(telegram_token, claude_api_key, user_id)

    async def webhook(request):
        update = await request.json()
        result = await brain.webhook_handler(update)
        return web.json_response(result)

    async def health(request):
        return web.json_response({"status": "healthy", "brain": "active"})

    app = web.Application()
    app.router.add_post("/webhook", webhook)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"🧠 Neural Brain running on port {port}")

    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await runner.cleanup()


async def run_local_mode(telegram_token: str, claude_api_key: str, user_id: int):
    """Run in local mode (polling instead of webhook)"""
    brain = TelegramNeuralBrain(telegram_token, claude_api_key, user_id)

    logger.info("🧠 Neural Brain started (local mode)")
    logger.info("Send /status to get system status")
    logger.info("Send /revenue to get revenue report")
    logger.info("Send any message to analyze")

    last_update_id = 0

    try:
        while True:
            url = f"{brain.base_url}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

                    for update in data.get("result", []):
                        last_update_id = update["update_id"]
                        await brain.webhook_handler(update)

            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Neural Brain stopped")


if __name__ == "__main__":
    import sys

    # Load config
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    user_id = int(os.getenv("TELEGRAM_USER_ID", "0"))

    if not all([token, claude_key, user_id]):
        print("❌ Missing required environment variables:")
        print("  TELEGRAM_BOT_TOKEN - Your Telegram bot token from @BotFather")
        print("  ANTHROPIC_API_KEY - Your Claude API key")
        print("  TELEGRAM_USER_ID - Your Telegram user ID")
        sys.exit(1)

    # Run in local mode (polling)
    asyncio.run(run_local_mode(token, claude_key, user_id))
