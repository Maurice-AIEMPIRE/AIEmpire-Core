#!/usr/bin/env python3
"""
GALAXIA TELEGRAM BOT - MINIMAL VERSION
Keine externen Dependencies außer: python-telegram-bot, redis
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
except ImportError:
    print("❌ python-telegram-bot nicht installiert")
    exit(1)

import redis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# ==================== REDIS STORAGE ====================

class RedisStore:
    def __init__(self):
        try:
            self.r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True
            )
            self.r.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis error: {e}")
            raise

    def add_message(self, user_id, role, text):
        key = f"conv:{user_id}"
        msg = {"role": role, "text": text, "time": datetime.utcnow().isoformat()}
        self.r.rpush(key, json.dumps(msg))
        self.r.ltrim(key, -20, -1)

    def get_conversation(self, user_id):
        key = f"conv:{user_id}"
        msgs = self.r.lrange(key, 0, -1)
        return [json.loads(m) for m in msgs]

store = RedisStore()

# ==================== BOT COMMANDS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    store.add_message(user_id, "system", "/start")

    msg = """🌌 **GALAXIA OS BOT**

Commands:
/status - System status
/revenue - Revenue pipeline
/evolve - Start evolution
/help - Show help

Natural language works too!"""

    await update.message.reply_text(msg, parse_mode="Markdown")
    store.add_message(user_id, "bot", msg)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    store.add_message(user_id, "system", "/help")

    msg = """📖 **HELP**
/start - Welcome
/status - System status
/revenue - Revenue info
/evolve - Evolution cycle
/learn - Learn topic
/tasks - Show tasks"""

    await update.message.reply_text(msg, parse_mode="Markdown")
    store.add_message(user_id, "bot", msg)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    store.add_message(user_id, "system", "/status")

    msg = f"""✅ **SYSTEM STATUS**
Redis: Connected ✅
Bot: Running ✅
Ollama: Waiting (optional)
Time: {datetime.utcnow().isoformat()}"""

    await update.message.reply_text(msg, parse_mode="Markdown")
    store.add_message(user_id, "bot", msg)


async def revenue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    store.add_message(user_id, "system", "/revenue")

    msg = """💰 **REVENUE PIPELINE**
Gumroad: Ready
Fiverr: Ready
Consulting: €2000-10000
Community: Ready

Total: €0 (pending)"""

    await update.message.reply_text(msg, parse_mode="Markdown")
    store.add_message(user_id, "bot", msg)


async def evolve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.replace("/evolve", "").strip()
    store.add_message(user_id, "user", f"/evolve {text}")

    msg = f"🧬 Evolution task queued\nPrompt: {text or 'Improve system'}\nStatus: Processing..."
    await update.message.reply_text(msg, parse_mode="Markdown")
    store.add_message(user_id, "bot", msg)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text.startswith("/"):
        return

    store.add_message(user_id, "user", text)

    # Echo back with context
    conv = store.get_conversation(user_id)
    context_str = f"User: {text}\nPrevious: {len(conv)} messages\n"

    msg = f"📝 Received: {text[:50]}...\n\n🤔 Processing...\n\n(Ollama integration available)"
    await update.message.reply_text(msg)
    store.add_message(user_id, "bot", msg)


async def error_handler(update, context):
    logger.error(f"Error: {context.error}\n{traceback.format_exc()}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Error occurred")


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not set in .env")
        exit(1)

    logger.info("🚀 Starting GALAXIA BOT...")

    app = Application.builder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("revenue", revenue))
    app.add_handler(CommandHandler("evolve", evolve))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.add_error_handler(error_handler)

    logger.info("✅ Bot initialized. Polling for messages...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
