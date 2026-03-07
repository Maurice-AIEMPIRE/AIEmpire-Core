#!/usr/bin/env python3
"""
GALAXIA OS TELEGRAM BOT - Main Bot Application
Controls: Revenue Engine, Evolution Engine, Self-Improvement, Neo4j, Redis, Ollama
Distributed, fault-tolerant, with automatic failover and monitoring
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from redis_state import StateStore

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/galaxia-bot.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# ==================== INITIALIZATION ====================

state_store = StateStore()
BOT_INSTANCE_ID = f"bot-{os.getenv('HOSTNAME', 'unknown')}-{os.getpid()}"

logger.info(f"🤖 GALAXIA BOT Starting: {BOT_INSTANCE_ID}")


# ==================== LLM INTEGRATION ====================

class GalaxiaLLM:
    """Interface to Ollama via LiteLLM endpoint"""

    def __init__(self):
        self.endpoint = os.getenv("MODEL_ENDPOINT", "http://localhost:4000/api/v1/chat/completions")
        self.primary_model = os.getenv("PRIMARY_MODEL", "qwen3:14b")
        self.fallback_model = os.getenv("FALLBACK_MODEL", "qwen3:8b")
        self.timeout = int(os.getenv("LLM_TIMEOUT", 120))

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """Generate response from LLM with fallback"""
        import httpx

        model = model or self.primary_model
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.endpoint, json=payload)
                resp.raise_for_status()
                data = resp.json()

                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"].strip()
                return "❌ Empty response from LLM"

        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout on {model}, trying fallback...")
            if model != self.fallback_model:
                return await self.generate(prompt, self.fallback_model)
            return "⚠️ LLM timeout - fallback also failed"

        except Exception as e:
            logger.error(f"❌ LLM Error ({model}): {e}")
            return f"❌ LLM Error: {str(e)[:100]}"


llm = GalaxiaLLM()


# ==================== BOT HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command - introduction"""
    user_id = update.effective_user.id

    # Check whitelist
    allowed = os.getenv("ALLOWED_CHAT_IDS", "").split(",")
    if str(user_id) not in allowed and allowed != [""]:
        await update.message.reply_text("❌ Unauthorized access")
        logger.warning(f"🚫 Unauthorized access from {user_id}")
        return

    state_store.append_message(str(user_id), "user", "/start")

    welcome_msg = """
🌌 **GALAXIA OS BOT** — Your Revenue & Evolution Control Center

Commands:
/help - Show all commands
/evolve - Start evolution cycle
/status - System status
/revenue - Revenue pipeline
/restart - Emergency restart (Plan B)
/tasks - Pending tasks
"""
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    state_store.append_message(str(user_id), "assistant", welcome_msg)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command - show all available commands"""
    help_text = """
🎯 **GALAXIA OS COMMANDS**

**System Control:**
/status - Show system health (Redis, Ollama, Services)
/restart - Restart all services (emergency)
/metrics - CPU, RAM, Active bots

**Revenue Pipeline:**
/revenue - Current revenue status
/leads - Active leads
/products - Product status

**Evolution & Learning:**
/evolve - Start evolution cycle
/learn <topic> - Learn from knowledge base
/improve - Run self-improvement

**Task Management:**
/tasks - Show pending tasks
/task <id> - Get task details
/cancel <id> - Cancel task

**Monitoring:**
/logs - Show last 20 error logs
/health - Detailed health check
/backup - Trigger backup now

**Configuration:**
/config - Show current config
/set <key> <value> - Update config

Use commands with natural language, e.g.:
"How is revenue today?"
"Start evolution"
"What's the system status?"
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """System status command"""
    user_id = update.effective_user.id
    state_store.append_message(str(user_id), "user", "/status")

    try:
        # Collect system status
        metrics = state_store.get_system_metrics()
        active_bots = state_store.get_active_bots()
        stats = state_store.get_stats()

        status_msg = f"""
🔍 **GALAXIA OS STATUS**

**Redis:**
- Memory: {stats.get('memory_used', 'N/A')}
- Clients: {stats.get('connected_clients', 'N/A')}
- Commands: {stats.get('total_commands', 'N/A')}

**Bots:**
- Active instances: {stats.get('active_bots', 0)}
- Instances: {', '.join(active_bots) if active_bots else 'None'}

**System Metrics:**
- CPU: {metrics.get('cpu_percent', 'N/A')}%
- RAM: {metrics.get('mem_percent', 'N/A')}%

**Timestamp:** {datetime.utcnow().isoformat()}
"""
        await update.message.reply_text(status_msg, parse_mode="Markdown")
        state_store.append_message(str(user_id), "assistant", status_msg)

    except Exception as e:
        error_msg = f"❌ Status check failed: {str(e)}"
        await update.message.reply_text(error_msg)
        logger.error(f"Status command error: {e}")


async def evolve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Evolution command - enqueue evolution task"""
    user_id = update.effective_user.id
    text = update.message.text.replace("/evolve", "").strip()

    state_store.append_message(str(user_id), "user", f"/evolve {text}")

    # Get conversation context
    conversation = state_store.get_conversation(str(user_id))

    # Enqueue evolution task
    task = {
        "command": "evolve",
        "user_id": user_id,
        "prompt": text or "Improve system based on recent performance",
        "conversation": conversation[-5:],
    }

    task_id = state_store.enqueue_task("galaxia.evolution", task)

    msg = f"🚀 Evolution started\nTask ID: `{task_id}`"
    await update.message.reply_text(msg, parse_mode="Markdown")
    state_store.append_message(str(user_id), "assistant", msg)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle natural language messages"""
    user_id = update.effective_user.id
    user_text = update.message.text

    if not user_text or user_text.startswith("/"):
        return

    state_store.append_message(str(user_id), "user", user_text)

    # Show typing indicator
    await update.message.chat.send_action("typing")

    try:
        # Generate response via LLM
        prompt = f"""You are GALAXIA OS Bot. Answer concisely about: {user_text}

Context: User {user_id} is asking about their revenue/evolution system."""

        response = await llm.generate(prompt)

        await update.message.reply_text(response, parse_mode="Markdown")
        state_store.append_message(str(user_id), "assistant", response)

    except Exception as e:
        error_msg = f"❌ Processing error: {str(e)[:100]}"
        await update.message.reply_text(error_msg)
        logger.error(f"Message handler error: {e}\n{traceback.format_exc()}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler - logs and notifies developer"""
    logger.error("Exception while handling update:", exc_info=context.error)

    # Format error
    tb_list = traceback.format_exception(type(context.error), context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Log to state store
    state_store.log_error(
        BOT_INSTANCE_ID,
        type(context.error).__name__,
        str(context.error)[:200],
        tb_string
    )

    # Notify developer
    dev_chat_id = os.getenv("DEVELOPER_CHAT_ID")
    if dev_chat_id:
        try:
            error_report = f"""⚠️ **BOT ERROR**
Instance: `{BOT_INSTANCE_ID}`
Type: `{type(context.error).__name__}`
Message: {str(context.error)[:200]}

```
{tb_string[:500]}
```
"""
            await context.bot.send_message(
                chat_id=int(dev_chat_id),
                text=error_report,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send error report to developer: {e}")

    # Notify user if available
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Developers have been notified."
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")


async def health_check(app: Application) -> None:
    """Periodic health check and heartbeat"""
    while True:
        try:
            # Update heartbeat
            state_store.set_bot_heartbeat(BOT_INSTANCE_ID)

            # Log stats
            stats = state_store.get_stats()
            logger.info(f"💚 Heartbeat: {stats}")

            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            await asyncio.sleep(5)


async def main() -> None:
    """Main bot initialization and startup"""

    # Verify Redis
    if not state_store.health_check():
        logger.error("❌ Cannot connect to Redis. Exiting.")
        return

    # Create application
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("evolve", evolve_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler
    app.add_error_handler(error_handler)

    # Health check task
    app.job_queue.run_repeating(
        lambda context: asyncio.create_task(health_check(app)),
        interval=10,
        first=5
    )

    logger.info(f"🚀 Starting bot: {BOT_INSTANCE_ID}")

    # Start bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    logger.info("🔄 Bot polling started. Waiting for messages...")
    await app.idle()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}\n{traceback.format_exc()}")
