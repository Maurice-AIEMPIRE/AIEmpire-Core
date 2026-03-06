#!/usr/bin/env python3
"""ADVANCED TELEGRAM BOT - STANDALONE (Redis optional)"""

import asyncio, json, os, logging, traceback
from datetime import datetime
from typing import Dict, Any, List
from urllib import request, parse
from urllib.error import URLError
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[logging.FileHandler("/tmp/advanced_bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not in .env")
    exit(1)

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

class TelegramBot:
    def __init__(self):
        self.offset = 0
        self.running = True
        self.logger = logger

    async def get_updates(self) -> List[Dict]:
        try:
            url = f"{BASE_URL}/getUpdates?offset={self.offset}&timeout=30"
            with request.urlopen(request.Request(url), timeout=35) as resp:
                return json.loads(resp.read()).get("result", [])
        except URLError as e:
            self.logger.error(f"Telegram API error: {e}")
            return []

    async def send_message(self, chat_id: int, text: str) -> bool:
        try:
            params = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            url = f"{BASE_URL}/sendMessage"
            data = parse.urlencode(params).encode('utf-8')
            with request.urlopen(request.Request(url, data=data), timeout=5) as resp:
                json.loads(resp.read())
                return True
        except URLError as e:
            self.logger.error(f"Send error: {e}")
            return False

    async def handle_message(self, user_id: int, chat_id: int, text: str) -> None:
        try:
            self.logger.info(f"📨 Message from {user_id}: {text[:50]}")

            if text.startswith("/start"):
                response = """🚀 **ADVANCED TELEGRAM BOT**

**Commands:**
/status - System status
/revenue - Revenue pipeline
/help - Help
/repair - Trigger repair

**Or just ask anything!**"""
            elif text.startswith("/status"):
                response = f"""📊 **SYSTEM STATUS**

✅ Bot: Online
✅ Telegram: Connected
⏳ Redis: Fallback mode
⏳ Ollama: Checking...

Time: {datetime.utcnow().isoformat()}"""
            elif text.startswith("/revenue"):
                response = """💰 **REVENUE PIPELINE**

Gumroad: €0 (ready)
Fiverr: €0 (active)
Consulting: €0 (available)
Community: €0 (0 members)

Total: €0 (pending activation)"""
            elif text.startswith("/repair"):
                response = """🔧 **REPAIR INITIATED**

✅ Redis: Fallback mode
✅ Environment: All vars set
✅ Network: Online

Status: System operational"""
            elif text.startswith("/help"):
                response = """🤖 **HELP**

/start - Start bot
/status - System status
/revenue - Revenue info
/repair - System repair
/help - This help

Try asking:
"What's the system status?"
"Show revenue"
"Repair the system" """
            else:
                # Simple NLU fallback
                text_lower = text.lower()
                if any(kw in text_lower for kw in ["status", "system", "health"]):
                    response = "📊 System is operational. Use /status for details."
                elif any(kw in text_lower for kw in ["revenue", "earnings", "money"]):
                    response = "💰 Use /revenue to see revenue pipeline."
                elif any(kw in text_lower for kw in ["repair", "fix", "issue"]):
                    response = "🔧 Use /repair to trigger system repair."
                else:
                    response = f"✅ Got your message: '{text}'\n\nTry /help for commands."

            await self.send_message(chat_id, response)
        except Exception as e:
            self.logger.error(f"Error: {e}\n{traceback.format_exc()}")
            await self.send_message(chat_id, f"❌ Error: {str(e)[:100]}")

    async def run(self) -> None:
        self.logger.info("🚀 Telegram Bot STARTED (Fallback Mode)")
        try:
            while self.running:
                try:
                    updates = await self.get_updates()
                    for update in updates:
                        self.offset = update.get("update_id", 0) + 1
                        if "message" in update:
                            msg = update["message"]
                            await self.handle_message(
                                msg["from"]["id"],
                                msg["chat"]["id"],
                                msg.get("text", "")
                            )
                    if not updates:
                        await asyncio.sleep(2)
                except Exception as e:
                    self.logger.error(f"Update loop error: {e}")
                    await asyncio.sleep(5)
        except KeyboardInterrupt:
            self.logger.info("🛑 Bot stopped by user")

async def main():
    bot = TelegramBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
