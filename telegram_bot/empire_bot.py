#!/usr/bin/env python3
"""
EMPIRE TELEGRAM BOT — Remote Control for AIEmpire
===================================================
Steuere dein gesamtes Empire vom Handy aus.
Verbindet Telegram mit deinem Mac, Ollama/Kimi und allen Empire-Systemen.

Features:
  - Shell-Befehle auf dem Mac ausfuehren
  - Empire Engine Befehle (scan, produce, revenue, auto...)
  - AI Chat via Ollama (lokal, kostenlos) oder Kimi (Cloud)
  - System Status + Health Checks
  - Sicherheit: Nur DEINE Telegram ID erlaubt

Setup:
  1. Telegram: @BotFather → /newbot → Token kopieren
  2. .env: TELEGRAM_BOT_TOKEN=dein-token
  3. .env: TELEGRAM_OWNER_ID=deine-chat-id
  4. python3 telegram_bot/empire_bot.py

Author: Maurice Pfeifer — AIEmpire
"""

import asyncio
import html
import json
import logging
import os
import signal
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ─── Path Setup ────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─── Load .env ─────────────────────────────────────────────────────
def _load_env():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_env()

# ─── Config ────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = os.getenv("TELEGRAM_OWNER_ID", "")  # Your Telegram user ID
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("empire_bot")

# ─── Telegram Bot (pure asyncio, no framework dependency) ──────────
# Uses Telegram Bot API directly via aiohttp — zero extra dependencies
# beyond what AIEmpire already has (aiohttp).

try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp not installed. Run: pip3 install aiohttp")
    sys.exit(1)


class EmpireBot:
    """Telegram Bot that controls the entire AIEmpire from your phone."""

    def __init__(self, token: str, owner_id: str):
        self.token = token
        self.owner_id = str(owner_id)
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.running = True
        self.session = None
        self.command_history = []

    # ─── Telegram API ──────────────────────────────────────────────

    async def _api(self, method: str, **kwargs) -> dict:
        """Call Telegram Bot API."""
        url = f"{self.base_url}/{method}"
        async with self.session.post(url, json=kwargs) as resp:
            data = await resp.json()
            if not data.get("ok"):
                log.error(f"Telegram API error: {data}")
            return data

    async def send(self, chat_id: str, text: str, parse_mode: str = "HTML"):
        """Send message, auto-split if too long."""
        # Telegram max message length is 4096
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            try:
                await self._api("sendMessage",
                    chat_id=chat_id,
                    text=chunk,
                    parse_mode=parse_mode,
                )
            except Exception:
                # Fallback without parse_mode if HTML is broken
                await self._api("sendMessage",
                    chat_id=chat_id,
                    text=chunk,
                )

    # ─── Security ──────────────────────────────────────────────────

    def _is_owner(self, message: dict) -> bool:
        """Only Maurice can use this bot."""
        user_id = str(message.get("from", {}).get("id", ""))
        if not self.owner_id:
            # SECURITY: owner_id MUST be configured in .env before bot can accept commands
            log.warning(f"SECURITY: TELEGRAM_OWNER_ID not configured. Message from {user_id} rejected.")
            return False
        return user_id == self.owner_id

    def _save_owner_id(self, user_id: str):
        """Save owner ID to .env for persistence."""
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            content = env_path.read_text()
            if "TELEGRAM_OWNER_ID" not in content:
                with open(env_path, "a") as f:
                    f.write(f"\n# Telegram Owner (auto-set on first message)\nTELEGRAM_OWNER_ID={user_id}\n")
                log.info(f"Owner ID saved: {user_id}")
        os.environ["TELEGRAM_OWNER_ID"] = user_id

    # ─── Command Handlers ─────────────────────────────────────────

    async def handle_message(self, message: dict):
        """Route incoming messages to handlers."""
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "").strip()

        if not text:
            return

        # Security check
        if not self._is_owner(message):
            await self.send(chat_id, "Zugriff verweigert. Nur Maurice darf diesen Bot nutzen.")
            return

        # Log
        log.info(f"Command: {text}")
        self.command_history.append({
            "time": datetime.now().isoformat(),
            "command": text,
        })

        # Route commands
        if text.startswith("/"):
            await self._handle_command(chat_id, text)
        elif text.startswith("!"):
            # Shell command: !ls -la
            await self._handle_shell(chat_id, text[1:].strip())
        elif text.startswith("$"):
            # Empire engine command: $scan, $revenue, $auto
            await self._handle_empire(chat_id, text[1:].strip())
        elif text.startswith("?"):
            # AI query: ?Erklaere mir BMA Normen
            await self._handle_ai(chat_id, text[1:].strip())
        else:
            # Default: AI chat
            await self._handle_ai(chat_id, text)

    async def _handle_command(self, chat_id: str, text: str):
        """Handle /slash commands."""
        cmd = text.split()[0].lower().replace("@", "").split("@")[0]
        args = text[len(cmd):].strip()

        handlers = {
            "/start": self._cmd_start,
            "/help": self._cmd_help,
            "/status": self._cmd_status,
            "/revenue": self._cmd_revenue,
            "/scan": self._cmd_scan,
            "/produce": self._cmd_produce,
            "/auto": self._cmd_auto,
            "/repair": self._cmd_repair,
            "/models": self._cmd_models,
            "/ip": self._cmd_ip,
            "/ssh": self._cmd_ssh_info,
            "/history": self._cmd_history,
            "/kill": self._cmd_kill,
        }

        handler = handlers.get(cmd)
        if handler:
            await handler(chat_id, args)
        else:
            await self.send(chat_id, f"Unbekannter Befehl: <code>{html.escape(cmd)}</code>\nTippe /help fuer alle Befehle.")

    # ─── Slash Commands ────────────────────────────────────────────

    async def _cmd_start(self, chat_id: str, args: str):
        user_id = str(chat_id)
        await self.send(chat_id, f"""<b>EMPIRE TELEGRAM BOT</b>
Willkommen, Maurice!

Deine Chat-ID: <code>{user_id}</code>
Verbunden mit: <code>{PROJECT_ROOT}</code>

<b>So steuerst du dein Empire:</b>

<b>Slash Commands:</b>
/status — System-Status
/revenue — Umsatz-Report
/scan — News scannen
/produce — Content generieren
/auto — Voller Zyklus
/repair — Auto-Repair
/models — Ollama Modelle
/ip — Mac IP-Adresse
/ssh — SSH Verbindungs-Info
/help — Alle Befehle

<b>Shortcuts:</b>
<code>!befehl</code> — Shell auf Mac ausfuehren
<code>$scan</code> — Empire Engine Befehl
<code>?frage</code> — AI fragen (Ollama/Kimi)
Einfach Text — AI Chat

Dein Empire wartet auf Befehle!""")

    async def _cmd_help(self, chat_id: str, args: str):
        await self.send(chat_id, """<b>EMPIRE BOT — Alle Befehle</b>

<b>System:</b>
/status — Systemstatus (Ollama, Services, RAM, CPU)
/models — Verfuegbare Ollama Modelle
/ip — Mac IP-Adressen (fuer Terminus)
/ssh — SSH Verbindungs-Anleitung
/repair — Auto-Repair ausfuehren
/kill — Prozess beenden

<b>Empire:</b>
/revenue — Umsatz-Report
/scan — News + Trends scannen
/produce — Content generieren
/auto — Voller autonomer Zyklus

<b>Direktbefehle:</b>
<code>!ls -la</code> — Shell-Befehl auf Mac
<code>!python3 script.py</code> — Python ausfuehren
<code>!ollama list</code> — Ollama Modelle
<code>!git status</code> — Git Status
<code>!brew services list</code> — macOS Services

<b>Empire Engine:</b>
<code>$scan</code> — = python3 empire_engine.py scan
<code>$revenue</code> — = python3 empire_engine.py revenue
<code>$auto</code> — = python3 empire_engine.py auto
<code>$godmode fix bug</code> — Godmode starten

<b>AI Chat:</b>
<code>?Was ist BMA DIN 14675</code> — AI fragt Ollama
Einfach Text tippen — AI Chat

<b>Sicherheit:</b>
Nur deine Telegram-ID hat Zugriff.""")

    async def _cmd_status(self, chat_id: str, args: str):
        """Full system status check."""
        await self.send(chat_id, "Pruefe System-Status...")

        checks = {}

        # Ollama
        try:
            async with self.session.get(f"{OLLAMA_URL}/api/version", timeout=aiohttp.ClientTimeout(total=3)) as r:
                if r.status == 200:
                    data = await r.json()
                    checks["Ollama"] = f"OK (v{data.get('version', '?')})"
                else:
                    checks["Ollama"] = "OFFLINE"
        except Exception:
            checks["Ollama"] = "OFFLINE"

        # System resources
        try:
            result = subprocess.run(
                ["python3", "-c", "import psutil; m=psutil.virtual_memory(); print(f'{m.percent}|{m.total//1024//1024//1024}')"],
                capture_output=True, text=True, timeout=5, cwd=str(PROJECT_ROOT),
            )
            if result.returncode == 0:
                pct, total = result.stdout.strip().split("|")
                checks["RAM"] = f"{pct}% von {total}GB"
            else:
                # Fallback without psutil
                result = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5)
                checks["RAM"] = "psutil nicht installiert"
        except Exception:
            checks["RAM"] = "Nicht pruefbar"

        # CPU
        try:
            result = subprocess.run(
                ["python3", "-c", "import psutil; print(f'{psutil.cpu_percent(interval=1)}%')"],
                capture_output=True, text=True, timeout=5,
            )
            checks["CPU"] = result.stdout.strip() if result.returncode == 0 else "?"
        except Exception:
            checks["CPU"] = "?"

        # Key files
        checks["empire_engine.py"] = "OK" if (PROJECT_ROOT / "empire_engine.py").exists() else "FEHLT"
        checks[".env"] = "OK" if (PROJECT_ROOT / ".env").exists() else "FEHLT"
        checks["antigravity/"] = "OK" if (PROJECT_ROOT / "antigravity").exists() else "FEHLT"
        checks["kimi_swarm/"] = "OK" if (PROJECT_ROOT / "kimi_swarm").exists() else "FEHLT"

        # Format output
        lines = ["<b>SYSTEM STATUS</b>\n"]
        for name, status in checks.items():
            icon = "+" if "OK" in str(status) or "%" in str(status) else "-"
            lines.append(f"  [{icon}] {name}: {status}")

        await self.send(chat_id, "\n".join(lines))

    async def _cmd_revenue(self, chat_id: str, args: str):
        await self._handle_empire(chat_id, "revenue")

    async def _cmd_scan(self, chat_id: str, args: str):
        await self._handle_empire(chat_id, "scan")

    async def _cmd_produce(self, chat_id: str, args: str):
        await self._handle_empire(chat_id, "produce")

    async def _cmd_auto(self, chat_id: str, args: str):
        await self.send(chat_id, "Starte autonomen Zyklus... (kann 1-2 Min dauern)")
        await self._handle_empire(chat_id, "auto")

    async def _cmd_repair(self, chat_id: str, args: str):
        await self.send(chat_id, "Starte Auto-Repair...")
        await self._handle_shell(chat_id, f"python3 {PROJECT_ROOT}/scripts/auto_repair.py")

    async def _cmd_models(self, chat_id: str, args: str):
        """List available Ollama models."""
        try:
            async with self.session.get(
                f"{OLLAMA_URL}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    models = data.get("models", [])
                    if models:
                        lines = ["<b>OLLAMA MODELLE</b>\n"]
                        for m in models:
                            name = m.get("name", "?")
                            size = m.get("size", 0) / 1024 / 1024 / 1024
                            lines.append(f"  <code>{name}</code> ({size:.1f}GB)")
                        await self.send(chat_id, "\n".join(lines))
                    else:
                        await self.send(chat_id, "Keine Modelle installiert.\n<code>!ollama pull qwen2.5-coder:7b</code>")
                else:
                    await self.send(chat_id, "Ollama nicht erreichbar. Starte: <code>!ollama serve</code>")
        except Exception:
            await self.send(chat_id, "Ollama nicht erreichbar.\nStarte: <code>!ollama serve &amp;</code>")

    async def _cmd_ip(self, chat_id: str, args: str):
        """Show Mac IP addresses for Terminus connection."""
        result = subprocess.run(
            ["bash", "-c", """
echo "=== NETZWERK-INTERFACES ==="
ifconfig 2>/dev/null | grep -E "^[a-z]|inet " | grep -v "127.0.0.1" || ip addr show 2>/dev/null | grep -E "^[0-9]|inet " | grep -v "127.0.0.1"
echo ""
echo "=== EXTERNE IP ==="
curl -s --connect-timeout 3 ifconfig.me 2>/dev/null || echo "Nicht erreichbar"
"""],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip() or "Konnte IPs nicht ermitteln"
        await self.send(chat_id, f"<b>MAC IP-ADRESSEN</b>\n<pre>{html.escape(output)}</pre>")

    async def _cmd_ssh_info(self, chat_id: str, args: str):
        """Show SSH connection info for Terminus."""
        # Get local IP
        ip_result = subprocess.run(
            ["bash", "-c", "ifconfig 2>/dev/null | grep 'inet 192' | head -1 | awk '{print $2}' || hostname -I 2>/dev/null | awk '{print $1}'"],
            capture_output=True, text=True, timeout=5,
        )
        local_ip = ip_result.stdout.strip() or "DEINE-MAC-IP"

        # Get username
        user = os.getenv("USER", "maurice")

        # Check SSH status
        ssh_result = subprocess.run(
            ["bash", "-c", "systemsetup -getremotelogin 2>/dev/null || echo 'SSH Status unbekannt'"],
            capture_output=True, text=True, timeout=5,
        )
        ssh_status = ssh_result.stdout.strip()

        await self.send(chat_id, f"""<b>TERMINUS / SSH VERBINDUNG</b>

<b>Status:</b> {html.escape(ssh_status)}

<b>Verbindungsdaten fuer Terminus:</b>
  Host: <code>{local_ip}</code>
  Port: <code>22</code>
  User: <code>{user}</code>
  Auth: Passwort oder SSH Key

<b>Falls SSH nicht aktiv ist:</b>
Auf dem Mac in den Systemeinstellungen:
  Einstellungen → Allgemein → Teilen → Entfernte Anmeldung (AN)

Oder im Terminal:
  <code>sudo systemsetup -setremotelogin on</code>

<b>Terminus App Setup:</b>
  1. Terminus oeffnen
  2. + New Host
  3. IP: <code>{local_ip}</code>
  4. Port: <code>22</code>
  5. User: <code>{user}</code>
  6. Passwort eingeben
  7. Connect!

<b>WICHTIG:</b>
  - Mac und Handy muessen im SELBEN WLAN sein
  - Oder: Tailscale/ZeroTier fuer Zugriff von ueberall""")

    async def _cmd_history(self, chat_id: str, args: str):
        """Show command history."""
        if not self.command_history:
            await self.send(chat_id, "Keine Befehle in dieser Session.")
            return
        lines = ["<b>LETZTE BEFEHLE</b>\n"]
        for entry in self.command_history[-20:]:
            lines.append(f"  {entry['time'][11:19]} | {html.escape(entry['command'])}")
        await self.send(chat_id, "\n".join(lines))

    async def _cmd_kill(self, chat_id: str, args: str):
        """Kill a process by name."""
        if not args:
            await self.send(chat_id, "Usage: /kill prozessname\nBeispiel: /kill ollama")
            return
        await self._handle_shell(chat_id, f"pkill -f {args} && echo 'Killed: {args}' || echo 'Nicht gefunden: {args}'")

    # ─── Shell Execution ───────────────────────────────────────────

    async def _handle_shell(self, chat_id: str, cmd: str):
        """Execute shell command on Mac and return output."""
        if not cmd:
            await self.send(chat_id, "Usage: <code>!befehl</code>\nBeispiel: <code>!ls -la</code>")
            return

        # Block dangerous commands
        dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb"]
        for d in dangerous:
            if d in cmd:
                await self.send(chat_id, f"BLOCKIERT: Gefaehrlicher Befehl erkannt.")
                return

        try:
            result = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=120,  # 2 min max
                cwd=str(PROJECT_ROOT),
                env={**os.environ, "PATH": f"/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}"},
            )

            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += ("\n--- STDERR ---\n" + result.stderr) if output else result.stderr

            output = output.strip() or "(Keine Ausgabe)"

            # Truncate very long output
            if len(output) > 3800:
                output = output[:1800] + "\n\n... (gekuerzt) ...\n\n" + output[-1800:]

            exit_icon = "OK" if result.returncode == 0 else f"Exit {result.returncode}"
            await self.send(chat_id, f"<b>$ {html.escape(cmd)}</b>\n<pre>{html.escape(output)}</pre>\n[{exit_icon}]")

        except subprocess.TimeoutExpired:
            await self.send(chat_id, f"TIMEOUT: Befehl hat laenger als 120s gedauert.\n<code>{html.escape(cmd)}</code>")
        except Exception as e:
            await self.send(chat_id, f"FEHLER: {html.escape(str(e))}")

    # ─── Empire Engine ─────────────────────────────────────────────

    async def _handle_empire(self, chat_id: str, cmd: str):
        """Execute empire_engine.py command."""
        if not cmd:
            await self.send(chat_id, "Usage: <code>$befehl</code>\nBeispiele: $scan, $revenue, $auto, $godmode fix xyz")
            return

        full_cmd = f"python3 {PROJECT_ROOT}/empire_engine.py {cmd}"
        await self._handle_shell(chat_id, full_cmd)

    # ─── AI Chat ───────────────────────────────────────────────────

    async def _handle_ai(self, chat_id: str, query: str):
        """Send query to Ollama (local) or Kimi (cloud fallback)."""
        if not query:
            await self.send(chat_id, "Stelle eine Frage oder schreib einfach los.")
            return

        # Try Ollama first (free, local)
        try:
            payload = {
                "model": "qwen2.5-coder:7b",  # Fast model
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Du bist der AI-Assistent im AIEmpire System von Maurice Pfeifer. "
                            "Maurice ist Elektrotechnikmeister mit 16 Jahren BMA-Expertise. "
                            "Antworte kurz, praezise und auf Deutsch. "
                            "Fokus: AI Agents, BMA (Brandmeldeanlagen), Revenue Generation, Automation."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                "stream": False,
            }

            async with self.session.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    answer = data.get("message", {}).get("content", "Keine Antwort")
                    model = data.get("model", "ollama")
                    await self.send(chat_id, f"<b>[{html.escape(model)}]</b>\n\n{html.escape(answer)}")
                    return
        except Exception as e:
            log.warning(f"Ollama failed: {e}")

        # Fallback: Kimi/Moonshot Cloud
        if MOONSHOT_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "moonshot-v1-8k",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Du bist der AI-Assistent von Maurice Pfeifer (AIEmpire). Antworte kurz und auf Deutsch.",
                        },
                        {"role": "user", "content": query},
                    ],
                }
                async with self.session.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        answer = data["choices"][0]["message"]["content"]
                        await self.send(chat_id, f"<b>[Kimi Cloud]</b>\n\n{html.escape(answer)}")
                        return
            except Exception as e:
                log.warning(f"Kimi failed: {e}")

        await self.send(chat_id,
            "Kein AI-Modell erreichbar.\n\n"
            "Starte Ollama: <code>!ollama serve &amp;</code>\n"
            "Oder setz MOONSHOT_API_KEY in .env"
        )

    # ─── Main Loop ─────────────────────────────────────────────────

    async def run(self):
        """Main polling loop."""
        log.info("Empire Bot startet...")

        self.session = aiohttp.ClientSession()

        # Verify token
        me = await self._api("getMe")
        if not me.get("ok"):
            log.error(f"Invalid token! Response: {me}")
            await self.session.close()
            return

        bot_name = me["result"].get("username", "?")
        log.info(f"Bot online: @{bot_name}")
        print(f"\n{'='*50}")
        print(f"  EMPIRE BOT ONLINE: @{bot_name}")
        print(f"  Warte auf Befehle von Telegram...")
        print(f"  Strg+C zum Beenden")
        print(f"{'='*50}\n")

        try:
            while self.running:
                try:
                    updates = await self._api(
                        "getUpdates",
                        offset=self.offset,
                        timeout=30,
                        allowed_updates=["message"],
                    )

                    for update in updates.get("result", []):
                        self.offset = update["update_id"] + 1
                        message = update.get("message")
                        if message:
                            try:
                                await self.handle_message(message)
                            except Exception as e:
                                log.error(f"Handler error: {e}")
                                traceback.print_exc()
                                chat_id = str(message["chat"]["id"])
                                await self.send(chat_id, f"Fehler: {html.escape(str(e))}")

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    log.error(f"Polling error: {e}")
                    await asyncio.sleep(5)

        finally:
            await self.session.close()
            log.info("Bot gestoppt.")


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    if not TELEGRAM_TOKEN:
        print("""
╔══════════════════════════════════════════════════════╗
║  EMPIRE TELEGRAM BOT — Setup                        ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  1. Oeffne Telegram und suche: @BotFather            ║
║  2. Sende: /newbot                                   ║
║  3. Name: AIEmpire Bot                               ║
║  4. Username: aiempire_maurice_bot (oder aehnlich)   ║
║  5. Kopiere den Token                                ║
║                                                      ║
║  6. Trage Token in .env ein:                         ║
║     TELEGRAM_BOT_TOKEN=dein-token-hier               ║
║                                                      ║
║  7. Starte erneut:                                   ║
║     python3 telegram_bot/empire_bot.py               ║
║                                                      ║
║  Der Bot erkennt dich automatisch beim ersten        ║
║  Nachricht und speichert deine ID.                   ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
""")
        sys.exit(1)

    bot = EmpireBot(TELEGRAM_TOKEN, OWNER_ID)

    # Graceful shutdown
    def _signal_handler(sig, frame):
        print("\nShutting down...")
        bot.running = False

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
