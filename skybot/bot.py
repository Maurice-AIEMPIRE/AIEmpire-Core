#!/usr/bin/env python3
"""
SkyBot Telegram Interface
==========================
Connects the SkyBot agent to Telegram.
Uses pure aiohttp (no extra framework needed).

Features:
  - Full AI agent with Claude tool use
  - Owner-only security
  - Conversation memory with /reset
  - Status, stats, and help commands
  - Inline progress messages while agent works

Usage:
  python3 -m skybot.bot
  # or
  python3 skybot/bot.py
"""

import asyncio
import html
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import aiohttp

# ─── Path setup ────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skybot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_ID, ANTHROPIC_API_KEY, MOONSHOT_API_KEY
from skybot.agent import SkyBotAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("skybot.bot")


class SkyBotTelegram:
    """Telegram bot that wraps the SkyBot agent."""

    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.owner_id = TELEGRAM_OWNER_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.running = True
        self.session: aiohttp.ClientSession | None = None
        self.agent = SkyBotAgent()
        self.processing = False  # Prevent concurrent requests

    # ─── Telegram API ──────────────────────────────────────────

    async def api(self, method: str, **kwargs) -> dict:
        async with self.session.post(f"{self.base_url}/{method}", json=kwargs) as resp:
            data = await resp.json()
            if not data.get("ok"):
                log.error(f"Telegram API error on {method}: {data}")
            return data

    async def send(self, chat_id: str, text: str, parse_mode: str = "HTML") -> dict | None:
        """Send message, auto-split at 4000 chars."""
        last_result = None
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            try:
                last_result = await self.api("sendMessage",
                    chat_id=chat_id,
                    text=chunk,
                    parse_mode=parse_mode,
                )
            except Exception:
                last_result = await self.api("sendMessage",
                    chat_id=chat_id,
                    text=chunk,
                )
        return last_result

    async def edit(self, chat_id: str, message_id: int, text: str):
        """Edit an existing message."""
        try:
            await self.api("editMessageText",
                chat_id=chat_id,
                message_id=message_id,
                text=text[:4000],
                parse_mode="HTML",
            )
        except Exception as e:
            log.debug(f"Failed to edit message: {e}")

    async def send_typing(self, chat_id: str):
        await self.api("sendChatAction", chat_id=chat_id, action="typing")

    # ─── Security ──────────────────────────────────────────────

    def is_owner(self, message: dict) -> bool:
        user_id = str(message.get("from", {}).get("id", ""))
        if not self.owner_id:
            self.owner_id = user_id
            self._save_owner_id(user_id)
            return True
        return user_id == self.owner_id

    def _save_owner_id(self, uid: str):
        env_path = PROJECT_ROOT / ".env"
        try:
            content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
            if "TELEGRAM_OWNER_ID" not in content:
                with open(env_path, "a", encoding="utf-8") as f:
                    f.write(f"\nTELEGRAM_OWNER_ID={uid}\n")
        except Exception as e:
            log.error(f"Failed to save TELEGRAM_OWNER_ID: {e}")
        os.environ["TELEGRAM_OWNER_ID"] = uid
        log.info(f"Owner ID set: {uid}")

    # ─── Message Handler ───────────────────────────────────────

    async def handle(self, message: dict):
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        if not chat_id:
            log.warning(f"Message missing chat.id, skipping")
            return
        text = message.get("text", "").strip()
        if not text:
            return

        if not self.is_owner(message):
            await self.send(chat_id, "Access denied.")
            return

        # Slash commands
        if text.startswith("/"):
            await self._handle_command(chat_id, text)
            return

        # Agent query
        await self._handle_agent(chat_id, text)

    async def _handle_command(self, chat_id: str, text: str):
        cmd = text.split()[0].lower().split("@")[0]
        args = text[len(cmd):].strip()

        if cmd == "/start":
            model = "Claude" if ANTHROPIC_API_KEY else ("Kimi" if MOONSHOT_API_KEY else "Ollama")
            await self.send(chat_id, f"""<b>SKYBOT — AI Agent</b>

Dein persoenlicher AI-Agent laeuft jetzt.
Aktives Modell: <b>{model}</b>

<b>Was ich kann:</b>
- Web durchsuchen und Seiten lesen
- Code schreiben und ausfuehren
- Dateien erstellen und verwalten
- GitHub durchsuchen (Trends, Repos, Code)
- Websites generieren (HTML/CSS/JS)

<b>Befehle:</b>
/help — Alle Befehle
/stats — Agent-Statistiken
/reset — Konversation zuruecksetzen
/model — Aktives Modell anzeigen

<b>Einfach losschreiben!</b>
Beispiele:
• "Suche nach AI Agent Frameworks auf GitHub"
• "Baue mir eine Landing Page fuer BMA Beratung"
• "Schreib ein Python Script das CSV in JSON konvertiert"
• "Was sind die Trending Repos auf GitHub heute?"
""")

        elif cmd == "/help":
            await self.send(chat_id, """<b>SKYBOT BEFEHLE</b>

/start — Willkommen + Info
/stats — Agent-Statistiken
/reset — Konversation loeschen (Neustart)
/model — Aktives AI-Modell anzeigen
/tools — Verfuegbare Tools anzeigen
/help — Diese Hilfe

<b>Einfach tippen fuer:</b>
- Web-Recherche
- Code-Generierung + Ausfuehrung
- Datei-Operationen
- GitHub-Suche
- Website-Builder
- Jede andere Frage

Der Agent entscheidet selbst welche Tools er braucht!""")

        elif cmd == "/stats":
            stats = self.agent.get_stats()
            await self.send(chat_id,
                f"<b>SKYBOT STATS</b>\n\n"
                f"Modell: <code>{stats['model']}</code>\n"
                f"Nachrichten: {stats['messages']}\n"
                f"Anthropic Key: {'Ja' if stats['has_anthropic_key'] else 'Nein'}\n"
                f"Moonshot Key: {'Ja' if stats['has_moonshot_key'] else 'Nein'}\n"
                f"Max Tool-Runden: {stats['max_tool_rounds']}"
            )

        elif cmd == "/reset":
            self.agent.reset()
            await self.send(chat_id, "Konversation zurueckgesetzt. Neuer Chat gestartet.")

        elif cmd == "/model":
            if ANTHROPIC_API_KEY:
                from skybot.config import CLAUDE_MODEL
                await self.send(chat_id,
                    f"<b>Aktives Modell:</b> Claude\n"
                    f"<code>{CLAUDE_MODEL}</code>\n\n"
                    f"Tool Use: Ja (5 Tools)\n"
                    f"Max Runden: {self.agent.get_stats()['max_tool_rounds']}"
                )
            elif MOONSHOT_API_KEY:
                await self.send(chat_id,
                    "<b>Aktives Modell:</b> Kimi/Moonshot Cloud\n"
                    "<code>moonshot-v1-8k</code>\n\n"
                    "Tool Use: Nein (nur Chat)\n"
                    "Fuer Tool Use: ANTHROPIC_API_KEY in .env setzen"
                )
            else:
                from skybot.config import OLLAMA_MODEL
                await self.send(chat_id,
                    f"<b>Aktives Modell:</b> Ollama (lokal)\n"
                    f"<code>{OLLAMA_MODEL}</code>\n\n"
                    f"Tool Use: Nein (nur Chat)\n"
                    f"Fuer Tool Use: ANTHROPIC_API_KEY in .env setzen"
                )

        elif cmd == "/tools":
            await self.send(chat_id, """<b>VERFUEGBARE TOOLS</b>

1. <b>web_search</b>
   Web-Suche (DuckDuckGo) oder URL abrufen

2. <b>code_exec</b>
   Python/Bash Code ausfuehren (Sandbox)

3. <b>file_ops</b>
   Dateien lesen/schreiben/loeschen im Workspace

4. <b>github_search</b>
   Repos, Code, Trending, User suchen

5. <b>web_builder</b>
   Websites generieren (HTML/CSS/JS)

<i>Tools werden automatisch vom Agent gewaehlt.</i>
<i>Fuer Tool Use muss ANTHROPIC_API_KEY gesetzt sein.</i>""")

        else:
            await self.send(chat_id, f"Unbekannt: {html.escape(cmd)}\nTippe /help")

    async def _handle_agent(self, chat_id: str, text: str):
        """Send message to agent, show progress, return response."""
        if self.processing:
            await self.send(chat_id, "Moment, ich arbeite noch an der vorherigen Anfrage...")
            return

        self.processing = True
        start = time.time()

        # Send "thinking" message
        thinking_msg = await self.send(chat_id, "Denke nach...")
        thinking_id = None
        if thinking_msg and thinking_msg.get("ok"):
            thinking_id = thinking_msg["result"]["message_id"]

        # Send typing indicator periodically
        typing_task = asyncio.create_task(self._keep_typing(chat_id))

        try:
            response = await self.agent.chat(text)
            elapsed = time.time() - start

            # Delete "thinking" message
            if thinking_id:
                await self.api("deleteMessage", chat_id=chat_id, message_id=thinking_id)

            # Send response
            footer = f"\n\n<i>[{elapsed:.1f}s]</i>"
            # Escape HTML in response but preserve our footer
            safe_response = html.escape(response)
            await self.send(chat_id, safe_response + footer)

        except Exception as e:
            log.error(f"Agent error: {e}")
            if thinking_id:
                await self.edit(chat_id, thinking_id, f"Fehler: {html.escape(str(e))}")
            else:
                await self.send(chat_id, f"Fehler: {html.escape(str(e))}")
        finally:
            typing_task.cancel()
            self.processing = False

    async def _keep_typing(self, chat_id: str):
        """Send typing indicator every 4 seconds."""
        try:
            while True:
                await self.send_typing(chat_id)
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass

    # ─── Main Loop ─────────────────────────────────────────────

    async def run(self):
        log.info("SkyBot starting...")
        self.session = aiohttp.ClientSession()

        # Verify token
        me = await self.api("getMe")
        if not me.get("ok"):
            log.error(f"Invalid token: {me}")
            await self.session.close()
            return

        bot_name = me["result"].get("username", "?")
        model = "Claude+Tools" if ANTHROPIC_API_KEY else ("Kimi" if MOONSHOT_API_KEY else "Ollama")

        print(f"""
{'='*55}
  SKYBOT ONLINE: @{bot_name}
  Model: {model}
  Tools: web_search, code_exec, file_ops, github_search, web_builder
  Waiting for Telegram messages...
  Ctrl+C to stop
{'='*55}
""")

        try:
            while self.running:
                try:
                    updates = await self.api(
                        "getUpdates",
                        offset=self.offset,
                        timeout=30,
                        allowed_updates=["message"],
                    )
                    for update in updates.get("result", []):
                        self.offset = update["update_id"] + 1
                        msg = update.get("message")
                        if msg:
                            try:
                                await self.handle(msg)
                            except Exception as e:
                                log.error(f"Handler error: {e}", exc_info=True)
                                chat_id = msg.get("chat", {}).get("id")
                                if chat_id:
                                    await self.send(str(chat_id), f"Error: {html.escape(str(e))}")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    log.error(f"Poll error: {e}")
                    await asyncio.sleep(5)
        finally:
            await self.session.close()
            log.info("SkyBot stopped.")


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("""
  SKYBOT — Setup Required

  1. Open Telegram → @BotFather → /newbot
  2. Copy the token
  3. Add to .env: TELEGRAM_BOT_TOKEN=your-token
  4. Add to .env: ANTHROPIC_API_KEY=your-key (for tool use)
  5. Run again: python3 -m skybot.bot
""")
        sys.exit(1)

    bot = SkyBotTelegram()

    def shutdown(sig, frame):
        print("\nShutting down...")
        bot.running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
