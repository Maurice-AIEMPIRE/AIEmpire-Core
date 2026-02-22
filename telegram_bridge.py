"""
Telegram <-> AIEmpire Bridge
==============================
Connects your iPhone (Telegram) to:
  1. LiteLLM Proxy (:4000) — AI chat with all models
  2. OpenClaw (:18789)     — Agent control & status
  3. Empire Engine         — Revenue, content, leads

Commands:
  /start      — Welcome + status
  /status     — System health check
  /models     — List available models
  /model X    — Switch model (e.g. /model ollama-qwen)
  /muscle X   — Use specific muscle (brain, coding, research, creative, fast)
  /revenue    — Revenue report
  /jobs       — Show cron jobs status
  /reset      — Clear conversation history
  Any text    — Chat with AI (routed through LiteLLM proxy)

Setup:
  1. Get token from @BotFather on Telegram
  2. Set TELEGRAM_BOT_TOKEN in .env
  3. Set TELEGRAM_ADMIN_CHAT_ID in .env (your personal chat ID)
  4. python3 telegram_bridge.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from antigravity.config import (
    LITELLM_PROXY_URL,
    LITELLM_API_KEY,
    OLLAMA_BASE_URL,
    OPENCLAW_URL,
)

logging.basicConfig(
    format="%(asctime)s [TelegramBridge] %(levelname)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
DEFAULT_MODEL = os.getenv("TELEGRAM_DEFAULT_MODEL", "ollama-qwen")

# Conversation history per chat (in-memory, resets on restart)
_conversations: dict[int, list[dict]] = {}
_active_model: dict[int, str] = {}

MAX_HISTORY = 20  # Keep last 20 messages per chat
MAX_RESPONSE_LENGTH = 4000  # Telegram message limit ~4096


# ─── LiteLLM Proxy Client ───────────────────────────────────────────

async def chat_litellm(messages: list[dict], model: str) -> dict:
    """Send chat to LiteLLM proxy at :4000."""
    import httpx

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{LITELLM_PROXY_URL}/v1/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {LITELLM_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    actual_model = data.get("model", model)

    return {
        "content": content,
        "model": actual_model,
        "tokens": usage.get("total_tokens", 0),
    }


async def check_litellm_health() -> dict:
    """Check LiteLLM proxy health."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{LITELLM_PROXY_URL}/health")
            return {"status": "online", "code": resp.status_code}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


async def check_ollama_health() -> dict:
    """Check Ollama health."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"status": "online", "models": models}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


async def get_proxy_models() -> list[str]:
    """Get available models from LiteLLM proxy."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{LITELLM_PROXY_URL}/v1/models",
                headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
            )
            data = resp.json()
            return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []


# ─── Telegram Bot ────────────────────────────────────────────────────

def is_admin(chat_id: int) -> bool:
    """Check if chat ID is the admin."""
    if not ADMIN_CHAT_ID:
        return True  # No restriction if not configured
    return str(chat_id) == str(ADMIN_CHAT_ID)


def get_history(chat_id: int) -> list[dict]:
    """Get conversation history for a chat."""
    if chat_id not in _conversations:
        _conversations[chat_id] = []
    return _conversations[chat_id]


def add_to_history(chat_id: int, role: str, content: str):
    """Add message to conversation history."""
    history = get_history(chat_id)
    history.append({"role": role, "content": content})
    # Trim to max history
    if len(history) > MAX_HISTORY * 2:
        _conversations[chat_id] = history[-MAX_HISTORY * 2:]


def get_model(chat_id: int) -> str:
    """Get active model for a chat."""
    return _active_model.get(chat_id, DEFAULT_MODEL)


def split_message(text: str, limit: int = MAX_RESPONSE_LENGTH) -> list[str]:
    """Split long messages for Telegram's 4096 char limit."""
    if len(text) <= limit:
        return [text]
    parts = []
    while text:
        if len(text) <= limit:
            parts.append(text)
            break
        # Find a good split point
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    return parts


async def run_bot():
    """Run the Telegram bot with polling."""
    from telegram import Update, BotCommand
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters,
    )

    # ─── Command Handlers ────────────────────────────────────────

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not is_admin(chat_id):
            await update.message.reply_text("Nicht autorisiert.")
            return

        health = await check_litellm_health()
        status_icon = "\u2705" if health["status"] == "online" else "\u274c"

        await update.message.reply_text(
            f"\U0001f680 *AIEmpire Telegram Bridge*\n\n"
            f"{status_icon} LiteLLM Proxy: {health['status']}\n"
            f"\U0001f916 Aktives Modell: `{get_model(chat_id)}`\n\n"
            f"*Commands:*\n"
            f"/status \u2014 System Health\n"
            f"/models \u2014 Verfuegbare Modelle\n"
            f"/model NAME \u2014 Modell wechseln\n"
            f"/muscle TYPE \u2014 Muscle waehlen\n"
            f"/revenue \u2014 Revenue Report\n"
            f"/jobs \u2014 Cron Jobs Status\n"
            f"/reset \u2014 Chat zuruecksetzen\n\n"
            f"Einfach schreiben = Chat mit AI",
            parse_mode="Markdown",
        )

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_chat.id):
            return

        await update.message.reply_text("\U0001f50d Pruefe Systeme...")

        litellm, ollama = await asyncio.gather(
            check_litellm_health(),
            check_ollama_health(),
        )

        li_icon = "\u2705" if litellm["status"] == "online" else "\u274c"
        ol_icon = "\u2705" if ollama["status"] == "online" else "\u274c"

        ollama_models = ""
        if ollama.get("models"):
            ollama_models = "\n".join(f"  \u2022 {m}" for m in ollama["models"])

        text = (
            f"\U0001f4ca *System Status*\n\n"
            f"{li_icon} *LiteLLM Proxy* ({LITELLM_PROXY_URL})\n"
            f"  Status: {litellm['status']}\n\n"
            f"{ol_icon} *Ollama* ({OLLAMA_BASE_URL})\n"
            f"  Status: {ollama['status']}\n"
        )
        if ollama_models:
            text += f"  Modelle:\n{ollama_models}\n"

        text += (
            f"\n\U0001f3af *OpenClaw* ({OPENCLAW_URL})\n"
            f"  Port: 18789\n\n"
            f"\U0001f916 *Aktives Modell:* `{get_model(update.effective_chat.id)}`"
        )

        await update.message.reply_text(text, parse_mode="Markdown")

    async def cmd_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_chat.id):
            return

        models = await get_proxy_models()
        current = get_model(update.effective_chat.id)

        if models:
            lines = []
            for m in models:
                marker = " \u2190 aktiv" if m == current else ""
                lines.append(f"  `{m}`{marker}")
            text = "\U0001f916 *Verfuegbare Modelle:*\n\n" + "\n".join(lines)
            text += f"\n\nWechseln: `/model MODELL_NAME`"
        else:
            text = (
                "\u26a0\ufe0f Proxy nicht erreichbar. Bekannte Modelle:\n"
                "  `ollama-qwen` (Qwen 14B)\n"
                "  `ollama-mistral` (Mistral 7B)\n"
                "  `gemini-flash`\n"
                "  `gemini-pro`\n"
                "  `kimi`\n"
                "  `deepseek-r1`"
            )

        await update.message.reply_text(text, parse_mode="Markdown")

    async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_chat.id):
            return

        if not context.args:
            await update.message.reply_text(
                f"Aktuell: `{get_model(update.effective_chat.id)}`\n"
                f"Usage: `/model ollama-qwen`",
                parse_mode="Markdown",
            )
            return

        model_name = context.args[0]
        _active_model[update.effective_chat.id] = model_name
        await update.message.reply_text(
            f"\u2705 Modell gewechselt: `{model_name}`",
            parse_mode="Markdown",
        )

    async def cmd_muscle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_chat.id):
            return

        muscle_models = {
            "brain": "gemini-pro",
            "coding": "ollama-qwen",
            "research": "kimi",
            "creative": "gemini-flash",
            "reasoning": "deepseek-r1",
            "fast": "ollama-mistral",
        }

        if not context.args:
            lines = [f"  `{k}` \u2192 {v}" for k, v in muscle_models.items()]
            await update.message.reply_text(
                "\U0001f4aa *Muscles:*\n\n" + "\n".join(lines) +
                "\n\nUsage: `/muscle coding`",
                parse_mode="Markdown",
            )
            return

        muscle = context.args[0].lower()
        if muscle not in muscle_models:
            await update.message.reply_text(
                f"\u274c Unbekannt: `{muscle}`\n"
                f"Verfuegbar: {', '.join(muscle_models.keys())}",
                parse_mode="Markdown",
            )
            return

        model_name = muscle_models[muscle]
        _active_model[update.effective_chat.id] = model_name
        await update.message.reply_text(
            f"\U0001f4aa Muscle `{muscle}` aktiviert \u2192 `{model_name}`",
            parse_mode="Markdown",
        )

    async def cmd_revenue(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_chat.id):
            return

        # Ask AI for revenue report
        add_to_history(update.effective_chat.id, "user",
            "Erstelle einen kurzen Revenue Report. "
            "Channels: Gumroad, Fiverr, Consulting, Community, X/Twitter. "
            "Format: Bullet points, aktueller Status, naechste Schritte.")

        messages = [
            {"role": "system", "content":
                "Du bist der AIEmpire Revenue Analyst. "
                "Antworte kurz und auf Deutsch. Bullet points."},
        ] + get_history(update.effective_chat.id)

        try:
            result = await chat_litellm(messages, get_model(update.effective_chat.id))
            add_to_history(update.effective_chat.id, "assistant", result["content"])
            for part in split_message(result["content"]):
                await update.message.reply_text(part)
        except Exception as e:
            await update.message.reply_text(f"\u274c Fehler: {e}")

    async def cmd_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_chat.id):
            return

        jobs_path = PROJECT_ROOT / "openclaw-config" / "jobs.json"
        if not jobs_path.exists():
            await update.message.reply_text("\u274c jobs.json nicht gefunden")
            return

        data = json.loads(jobs_path.read_text())
        jobs = data.get("jobs", [])

        lines = ["\U0001f4cb *OpenClaw Cron Jobs:*\n"]
        for job in jobs:
            enabled = "\u2705" if job.get("enabled") else "\u274c"
            schedule = job.get("schedule", {}).get("expr", "?")
            state = job.get("state", {})
            last_status = state.get("lastStatus", "never")
            lines.append(
                f"{enabled} `{schedule}` {job['name']}\n"
                f"   Agent: {job['agentId']} | Last: {last_status}"
            )

        text = "\n".join(lines)
        for part in split_message(text):
            await update.message.reply_text(part, parse_mode="Markdown")

    async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_chat.id):
            return

        chat_id = update.effective_chat.id
        _conversations[chat_id] = []
        await update.message.reply_text(
            "\U0001f5d1 Chat-Verlauf zurueckgesetzt.\n"
            f"Modell: `{get_model(chat_id)}`",
            parse_mode="Markdown",
        )

    # ─── Message Handler (Chat) ──────────────────────────────────

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not is_admin(chat_id):
            return

        user_text = update.message.text
        if not user_text:
            return

        model = get_model(chat_id)
        add_to_history(chat_id, "user", user_text)

        # Build messages with system prompt + history
        system_prompt = (
            "Du bist der AIEmpire AI-Assistent von Maurice Pfeifer. "
            "Du hilfst bei: Business-Strategie, Content-Erstellung, "
            "Code-Entwicklung, Lead-Generierung, und Revenue-Optimierung. "
            "Antworte praezise, auf Deutsch wenn der User Deutsch schreibt. "
            "Du hast Zugriff auf: LiteLLM Proxy, Ollama, OpenClaw, "
            "und das gesamte AIEmpire-System."
        )

        messages = [
            {"role": "system", "content": system_prompt},
        ] + get_history(chat_id)

        # Show typing indicator
        await update.effective_chat.send_action("typing")

        try:
            start = time.time()
            result = await chat_litellm(messages, model)
            elapsed = time.time() - start

            add_to_history(chat_id, "assistant", result["content"])

            # Add model/timing footer
            footer = f"\n\n_\u2014 {result['model']} | {result['tokens']} tokens | {elapsed:.1f}s_"

            response = result["content"]
            parts = split_message(response)

            # Add footer to last part
            if parts:
                last = parts[-1] + footer
                if len(last) > MAX_RESPONSE_LENGTH:
                    parts.append(footer)
                else:
                    parts[-1] = last

            for part in parts:
                await update.message.reply_text(part, parse_mode="Markdown")

        except Exception as e:
            log.error(f"Chat error: {e}")
            # Try without markdown if it fails
            error_msg = f"Fehler: {e}\n\nModell: {model}\nProxy: {LITELLM_PROXY_URL}"
            await update.message.reply_text(error_msg)

    # ─── Build & Run ─────────────────────────────────────────────

    if not BOT_TOKEN:
        log.error(
            "TELEGRAM_BOT_TOKEN nicht gesetzt!\n"
            "1. Oeffne Telegram -> @BotFather\n"
            "2. /newbot -> Name vergeben -> Token kopieren\n"
            "3. In .env eintragen: TELEGRAM_BOT_TOKEN=dein-token\n"
            "4. Starte erneut: python3 telegram_bridge.py"
        )
        sys.exit(1)

    log.info(f"Starte Telegram Bridge...")
    log.info(f"  LiteLLM Proxy: {LITELLM_PROXY_URL}")
    log.info(f"  Ollama:        {OLLAMA_BASE_URL}")
    log.info(f"  OpenClaw:      {OPENCLAW_URL}")
    log.info(f"  Default Model: {DEFAULT_MODEL}")
    if ADMIN_CHAT_ID:
        log.info(f"  Admin Chat ID: {ADMIN_CHAT_ID}")
    else:
        log.warning("  TELEGRAM_ADMIN_CHAT_ID nicht gesetzt — Bot offen fuer ALLE!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("models", cmd_models))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("muscle", cmd_muscle))
    app.add_handler(CommandHandler("revenue", cmd_revenue))
    app.add_handler(CommandHandler("jobs", cmd_jobs))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set bot commands for Telegram menu
    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("start", "Start + Status"),
            BotCommand("status", "System Health Check"),
            BotCommand("models", "Verfuegbare Modelle"),
            BotCommand("model", "Modell wechseln"),
            BotCommand("muscle", "Muscle waehlen (brain/coding/...)"),
            BotCommand("revenue", "Revenue Report"),
            BotCommand("jobs", "Cron Jobs Status"),
            BotCommand("reset", "Chat zuruecksetzen"),
        ])
        log.info("Bot Commands registriert. Bot ist ONLINE!")

    app.post_init = post_init

    # Run with polling (kein Webhook noetig!)
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    log.info("Telegram Bridge laeuft. Ctrl+C zum Stoppen.")

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        log.info("Stoppe Telegram Bridge...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(run_bot())
