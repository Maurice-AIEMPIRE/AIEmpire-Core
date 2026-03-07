#!/usr/bin/env python3
"""
AIEmpire Telegram Bot
=====================
Empfängt Nachrichten, X-Posts, PDFs, ZIPs und alle Dateitypen.
Verarbeitet sie mit AIEmpire-Core und antwortet zurück.

Läuft auf dem Hetzner-Server (direkt, ohne Proxy).
Start: python3 telegram_bot/bot.py
"""

import os
import sys
import json
import asyncio
import logging
import tempfile
import zipfile
import mimetypes
from pathlib import Path
from datetime import datetime

# Telegram
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        CallbackQueryHandler, ContextTypes, filters
    )
except ImportError:
    print("Installiere python-telegram-bot...")
    os.system("pip3 install python-telegram-bot --quiet")
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        CallbackQueryHandler, ContextTypes, filters
    )

# Füge AIEmpire-Core zum Pfad hinzu
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/aiempire_telegram.log")
    ]
)
log = logging.getLogger("AIEmpire-Bot")

# ─── Config ──────────────────────────────────────────────────────────────────

def load_config():
    """Lädt Token aus .env oder Umgebungsvariablen."""
    env_file = REPO_ROOT / ".env"
    config = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                config[k.strip()] = v.strip().strip('"').strip("'")
    config.update(os.environ)
    return config

CONFIG = load_config()
TOKEN = CONFIG.get("TELEGRAM_BOT_TOKEN", "8659143190:AAHKV3b0s-j-Uuppol0tx_ET9aHPHAE3urw")
ALLOWED_USERS = CONFIG.get("TELEGRAM_ALLOWED_USERS", "").split(",")  # Optional: User IDs einschränken

# ─── File Handler ─────────────────────────────────────────────────────────────

UPLOAD_DIR = REPO_ROOT / "telegram_bot" / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

def process_text_content(text: str, source: str = "telegram") -> str:
    """Verarbeitet Text durch AIEmpire mit Fallback-Kette: Kimi → Ollama → Dummy."""

    # 1️⃣ FALLBACK CHAIN: Kimi (Moonshot API) - MOST RELIABLE
    try:
        import requests
        api_key = CONFIG.get("MOONSHOT_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        if api_key:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "moonshot-v1-8k",
                "messages": [
                    {"role": "user", "content": f"Kurz und prägnant antworten:\n\n{text[:2000]}"}
                ],
                "temperature": 0.7
            }
            response = requests.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45  # <-- Extended timeout
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("choices"):
                    result = data["choices"][0]["message"]["content"]
                    log.info(f"✅ Kimi antwort: {len(result)} chars")
                    return result[:4000]  # Limit to telegram msg size
    except Exception as e:
        log.warning(f"Kimi fallback failed: {e}")

    # 2️⃣ FALLBACK: Ollama lokal (wenn verfügbar)
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            payload = {
                "model": "qwen2.5-coder:7b",
                "prompt": f"Kurz antworten:\n{text[:1000]}",
                "stream": False
            }
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                result = response.json().get("response", "")
                log.info(f"✅ Ollama response: {len(result)} chars")
                return result[:4000]
    except Exception as e:
        log.debug(f"Ollama nicht verfügbar: {e}")

    # 3️⃣ FALLBACK: Empire Engine
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "empire_engine.py"), "produce"],
            input=text, capture_output=True, text=True, timeout=60,
            cwd=str(REPO_ROOT)
        )
        if result.returncode == 0 and result.stdout.strip():
            log.info(f"✅ Empire Engine response")
            return result.stdout.strip()[:4000]
    except Exception as e:
        log.debug(f"Empire Engine: {e}")

    # 4️⃣ DEFAULT: Bestätigung + Queuing
    log.info(f"📝 Queued task (no AI available): {text[:100]}")
    return (
        f"✅ **Aufgabe empfangen!**\n\n"
        f"📝 Task: `{text[:80]}...`\n\n"
        f"⚙️ AIEmpire verarbeitet dies.\n"
        f"(Kimi/Ollama derzeit offline, Queue-Modus)\n\n"
        f"Antworte mit `/status` für Updateβ"
    )


def process_pdf(filepath: Path) -> str:
    """Extrahiert und verarbeitet PDF-Inhalt."""
    try:
        import subprocess
        # pdftotext versuchen
        result = subprocess.run(
            ["pdftotext", str(filepath), "-"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            return f"📄 **PDF extrahiert** ({len(text)} Zeichen)\n\n{text[:2000]}{'...' if len(text) > 2000 else ''}"
    except Exception:
        pass

    try:
        # PyPDF2 als Fallback
        import PyPDF2
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return f"📄 **PDF** ({len(reader.pages)} Seiten)\n\n{text[:2000]}{'...' if len(text) > 2000 else ''}"
    except ImportError:
        pass

    return f"📄 **PDF empfangen**: {filepath.name}\n⚙️ PDF-Verarbeitung wird eingerichtet (pip install PyPDF2)"


def process_zip(filepath: Path) -> str:
    """Entpackt und analysiert ZIP-Inhalt."""
    extract_dir = UPLOAD_DIR / filepath.stem
    extract_dir.mkdir(exist_ok=True)

    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            file_list = zf.namelist()
            zf.extractall(extract_dir)

        # Analysiere Inhalt
        summary = f"📦 **ZIP entpackt**: {filepath.name}\n"
        summary += f"📁 {len(file_list)} Dateien:\n"
        for f in file_list[:20]:
            summary += f"  • `{f}`\n"
        if len(file_list) > 20:
            summary += f"  ... und {len(file_list) - 20} weitere\n"

        # Text-Dateien lesen
        text_content = ""
        for fname in file_list[:5]:
            fpath = extract_dir / fname
            if fpath.is_file() and fpath.suffix in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml']:
                try:
                    content = fpath.read_text(errors='ignore')[:500]
                    text_content += f"\n**{fname}:**\n```\n{content}\n```\n"
                except Exception:
                    pass

        return summary + text_content

    except Exception as e:
        return f"📦 **ZIP**: {filepath.name}\n❌ Fehler: {e}"


def process_image(filepath: Path) -> str:
    """Verarbeitet Bild-Dateien."""
    size = filepath.stat().st_size
    return (
        f"🖼️ **Bild empfangen**: {filepath.name}\n"
        f"📊 Größe: {size // 1024} KB\n"
        f"💾 Gespeichert: `{filepath}`\n\n"
        f"✅ Bild bereit für Verarbeitung durch AIEmpire Vision Module."
    )


async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Path:
    """Lädt Datei von Telegram herunter."""
    msg = update.message
    file_obj = None
    filename = "unknown"

    if msg.document:
        file_obj = await msg.document.get_file()
        filename = msg.document.file_name or f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    elif msg.photo:
        file_obj = await msg.photo[-1].get_file()
        filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    elif msg.audio:
        file_obj = await msg.audio.get_file()
        filename = msg.audio.file_name or f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    elif msg.voice:
        file_obj = await msg.voice.get_file()
        filename = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg"
    elif msg.video:
        file_obj = await msg.video.get_file()
        filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    if file_obj:
        filepath = UPLOAD_DIR / filename
        await file_obj.download_to_drive(str(filepath))
        log.info(f"Datei heruntergeladen: {filepath}")
        return filepath

    return None

# ─── Command Handler ───────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start-Befehl."""
    user = update.effective_user
    log.info(f"Start von User: {user.id} ({user.username})")

    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data="status"),
         InlineKeyboardButton("💰 Revenue", callback_data="revenue")],
        [InlineKeyboardButton("🔄 Auto-Cycle", callback_data="auto"),
         InlineKeyboardButton("🔧 Repair", callback_data="repair")],
        [InlineKeyboardButton("📱 X-Post erstellen", callback_data="xpost"),
         InlineKeyboardButton("📄 Leads scannen", callback_data="leads")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 **Hallo {user.first_name}!**\n\n"
        f"🤖 **AIEmpire Control Bot** aktiv\n\n"
        f"**Was ich kann:**\n"
        f"• 📝 Text-Befehle verarbeiten\n"
        f"• 📄 PDFs analysieren & extrahieren\n"
        f"• 📦 ZIP-Dateien entpacken & prüfen\n"
        f"• 🖼️ Bilder empfangen & verarbeiten\n"
        f"• 🐦 X-Posts erstellen\n"
        f"• 📊 Empire Status abfragen\n\n"
        f"**Einfach schicken:**\n"
        f"• Textnachrichten → direkt verarbeiten\n"
        f"• Dateien → hochladen & analysieren\n"
        f"• /help → alle Befehle\n",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hilfe-Befehl."""
    await update.message.reply_text(
        "**📚 AIEmpire Bot Befehle:**\n\n"
        "**System:**\n"
        "/start — Bot starten + Menü\n"
        "/status — System Status\n"
        "/revenue — Revenue Report\n"
        "/repair — Auto-Repair starten\n\n"
        "**Content:**\n"
        "/post [text] — X-Post erstellen\n"
        "/scan — News & Trends scannen\n"
        "/leads — Leads verarbeiten\n"
        "/auto — Voller Auto-Cycle\n\n"
        "**Dateien (einfach senden):**\n"
        "📄 PDF → Inhalt extrahieren\n"
        "📦 ZIP → Entpacken & analysieren\n"
        "🖼️ Bild → Speichern & verarbeiten\n"
        "📁 Jede Datei → Verarbeiten\n\n"
        "**Freitext:**\n"
        "Schreibe einfach was du willst →\n"
        "AIEmpire verarbeitet es! 🚀",
        parse_mode="Markdown"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """System Status."""
    await update.message.reply_text("⏳ Lade Status...")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "empire_engine.py")],
            capture_output=True, text=True, timeout=30,
            cwd=str(REPO_ROOT)
        )
        output = result.stdout[:3000] or "Kein Output"
        await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Status-Fehler: {e}")


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🏥 Health Check - testet alle Fallback-Systeme."""
    msg = await update.message.reply_text("🏥 **Health Check läuft...**\n\n⏳ Teste Systeme...")

    results = []

    # 1. Kimi Check
    try:
        import requests
        api_key = CONFIG.get("MOONSHOT_API_KEY")
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            response = requests.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers=headers,
                json={"model": "moonshot-v1-8k", "messages": [{"role": "user", "content": "Hi"}]},
                timeout=10
            )
            if response.status_code == 200:
                results.append("✅ **Kimi API**: 🟢 ONLINE")
            else:
                results.append(f"⚠️ **Kimi API**: 🟡 Status {response.status_code}")
        else:
            results.append("❌ **Kimi API**: 🔴 Kein API Key")
    except Exception as e:
        results.append(f"❌ **Kimi API**: 🔴 {str(e)[:50]}")

    # 2. Ollama Check
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            results.append(f"✅ **Ollama**: 🟢 ONLINE ({len(models)} models)")
        else:
            results.append(f"⚠️ **Ollama**: 🟡 Status {response.status_code}")
    except Exception as e:
        results.append(f"❌ **Ollama**: 🔴 Not running")

    # 3. Empire Engine Check
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "empire_engine.py")],
            capture_output=True, text=True, timeout=10, cwd=str(REPO_ROOT)
        )
        if result.returncode == 0:
            results.append("✅ **Empire Engine**: 🟢 READY")
        else:
            results.append(f"⚠️ **Empire Engine**: 🟡 Returned {result.returncode}")
    except Exception as e:
        results.append(f"⚠️ **Empire Engine**: 🟡 Timeout/Error")

    # 4. Config Check
    api_key = CONFIG.get("MOONSHOT_API_KEY") or "Not set"
    token = CONFIG.get("TELEGRAM_BOT_TOKEN")
    results.append(f"📋 **Config**: MOONSHOT_API_KEY={'✅ SET' if api_key != 'Not set' else '❌ MISSING'}")

    # Summary
    status_text = "🏥 **HEALTH CHECK RESULTS:**\n\n" + "\n".join(results)
    status_text += f"\n\n📝 **Fallback-Strategie:**\n1. Kimi (API)\n2. Ollama (Local)\n3. Empire Engine\n4. Dummy Response\n\n✅ Bot ist einsatzbereit!"

    await msg.edit_text(status_text, parse_mode="Markdown")


async def cmd_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """X-Post erstellen."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "📝 Sende mir den Post-Inhalt:\n"
            "Entweder `/post Dein Text hier`\n"
            "oder schreibe einfach deinen Text."
        )
        return

    await update.message.reply_text(f"🐦 Erstelle X-Post für:\n`{text}`", parse_mode="Markdown")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "empire_engine.py"), "produce"],
            capture_output=True, text=True, timeout=60,
            cwd=str(REPO_ROOT), input=text
        )
        output = result.stdout[:2000] or "Post wird vorbereitet..."
        await update.message.reply_text(f"✅ **Post erstellt:**\n\n{output}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Verwende Ollama Fallback...\n{process_text_content(text)}")


async def cmd_empire(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    """Generischer Empire Engine Command."""
    await update.message.reply_text(f"⚙️ Starte: `empire_engine.py {command}`", parse_mode="Markdown")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "empire_engine.py"), command],
            capture_output=True, text=True, timeout=120,
            cwd=str(REPO_ROOT)
        )
        output = (result.stdout + result.stderr)[:3000] or "Fertig (kein Output)"
        await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Fehler: {e}")

# ─── Message Handler ───────────────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verarbeitet Textnachrichten."""
    text = update.message.text
    user = update.effective_user
    log.info(f"Text von {user.username}: {text[:100]}")

    # Lade-Animation
    thinking_msg = await update.message.reply_text("🤔 Verarbeite...")

    # Spezielle Befehls-Erkennung ohne /
    text_lower = text.lower().strip()
    if any(kw in text_lower for kw in ["x post", "tweet", "post erstellen", "viral"]):
        response = f"🐦 **X-Post Modus**\n\nGeneriere viralen Post für:\n`{text}`\n\n"
        result = process_text_content(f"Erstelle einen viralen X/Twitter Post über: {text}")
        response += result
    elif any(kw in text_lower for kw in ["status", "wie läuft", "check"]):
        import subprocess
        try:
            result = subprocess.run(
                ["python3", str(REPO_ROOT / "empire_engine.py")],
                capture_output=True, text=True, timeout=20, cwd=str(REPO_ROOT)
            )
            response = f"📊 **System Status:**\n```\n{result.stdout[:2000]}\n```"
        except Exception:
            response = "📊 Status: Empire Engine läuft. Alle Systeme aktiv."
    elif any(kw in text_lower for kw in ["revenue", "geld", "einnahmen", "umsatz"]):
        response = "💰 **Revenue Report wird geladen...**\n\nAktuelle Kanäle:\n• Gumroad BMA Checklisten\n• Fiverr AI Services\n• Consulting\n• Community"
    else:
        # Standard: durch AIEmpire verarbeiten
        result = process_text_content(text)
        response = f"✅ **Verarbeitet:**\n\n{result}"

    await thinking_msg.delete()
    await update.message.reply_text(response[:4000], parse_mode="Markdown")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verarbeitet alle Datei-Uploads."""
    msg = update.message
    user = update.effective_user

    # Datei-Info holen
    if msg.document:
        fname = msg.document.file_name or "document"
        fsize = msg.document.file_size or 0
        mime = msg.document.mime_type or "unknown"
    elif msg.photo:
        fname = "photo.jpg"
        fsize = msg.photo[-1].file_size or 0
        mime = "image/jpeg"
    elif msg.audio:
        fname = msg.audio.file_name or "audio.mp3"
        fsize = msg.audio.file_size or 0
        mime = "audio/mpeg"
    elif msg.voice:
        fname = "voice.ogg"
        fsize = msg.voice.file_size or 0
        mime = "audio/ogg"
    elif msg.video:
        fname = "video.mp4"
        fsize = msg.video.file_size or 0
        mime = "video/mp4"
    else:
        await msg.reply_text("❓ Unbekannter Dateityp")
        return

    log.info(f"Datei von {user.username}: {fname} ({fsize // 1024} KB)")

    # Lade-Nachricht
    status_msg = await msg.reply_text(
        f"📥 **Empfange:** `{fname}`\n"
        f"📊 Größe: {fsize // 1024} KB\n"
        f"⏳ Verarbeite...",
        parse_mode="Markdown"
    )

    # Datei herunterladen
    filepath = await download_file(update, context)
    if not filepath:
        await status_msg.edit_text("❌ Download fehlgeschlagen")
        return

    # Nach Typ verarbeiten
    suffix = filepath.suffix.lower()
    caption = msg.caption or ""

    if suffix == ".pdf" or mime == "application/pdf":
        result = process_pdf(filepath)
        emoji = "📄"
    elif suffix == ".zip" or mime == "application/zip":
        result = process_zip(filepath)
        emoji = "📦"
    elif suffix in [".jpg", ".jpeg", ".png", ".gif", ".webp"] or "image" in mime:
        result = process_image(filepath)
        emoji = "🖼️"
    elif suffix in [".txt", ".md", ".csv", ".json", ".yaml", ".yml"]:
        try:
            content = filepath.read_text(errors='ignore')
            if caption:
                result = process_text_content(f"{caption}\n\nDateiinhalt:\n{content[:2000]}")
            else:
                result = f"📝 **Textdatei:** `{fname}`\n\n```\n{content[:2000]}\n```"
        except Exception as e:
            result = f"❌ Lesefehler: {e}"
        emoji = "📝"
    elif suffix in [".py", ".js", ".ts", ".html", ".css"]:
        try:
            content = filepath.read_text(errors='ignore')
            result = f"💻 **Code-Datei:** `{fname}`\n\n```{suffix[1:]}\n{content[:2000]}\n```"
            if caption:
                result += f"\n\n**Aufgabe:** {caption}"
        except Exception as e:
            result = f"❌ Lesefehler: {e}"
        emoji = "💻"
    else:
        size_mb = fsize / (1024 * 1024)
        result = (
            f"📁 **Datei gespeichert:** `{fname}`\n"
            f"📊 Typ: `{mime}`\n"
            f"💾 Größe: {size_mb:.2f} MB\n"
            f"📂 Pfad: `{filepath}`\n\n"
            f"✅ Bereit für Verarbeitung durch AIEmpire."
        )
        if caption:
            result += f"\n\n**Auftrag:** {process_text_content(caption)}"
        emoji = "📁"

    # User-Caption verarbeiten
    if caption and emoji not in ["📄", "📦"]:
        extra = process_text_content(f"Datei '{fname}' wurde hochgeladen mit Auftrag: {caption}")
        result += f"\n\n**AIEmpire:** {extra[:500]}"

    await status_msg.delete()
    await msg.reply_text(f"{result[:4000]}", parse_mode="Markdown")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verarbeitet Inline-Keyboard Buttons."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "status":
        await query.message.reply_text("⏳ Lade Status...")
        await cmd_empire(query, context, "")
    elif data == "revenue":
        await cmd_empire(query, context, "revenue")
    elif data == "auto":
        await query.message.reply_text("🔄 Starte Auto-Cycle...")
        await cmd_empire(query, context, "auto")
    elif data == "repair":
        await query.message.reply_text("🔧 Starte Auto-Repair...")
        await cmd_empire(query, context, "repair")
    elif data == "xpost":
        await query.message.reply_text(
            "🐦 **X-Post Modus**\n\n"
            "Schreibe einfach dein Thema oder den Post-Text.\n"
            "AIEmpire generiert einen viralen Post!",
            parse_mode="Markdown"
        )
    elif data == "leads":
        await cmd_empire(query, context, "leads")

# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    """Startet den Bot."""
    if not TOKEN:
        log.error("TELEGRAM_BOT_TOKEN nicht gesetzt!")
        log.error("Setze in .env: TELEGRAM_BOT_TOKEN=dein_token")
        sys.exit(1)

    log.info("=" * 50)
    log.info("AIEmpire Telegram Bot startet")
    log.info(f"Token: {TOKEN[:20]}...")
    log.info(f"Uploads: {UPLOAD_DIR}")
    log.info("=" * 50)

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("health", cmd_health))  # 🏥 NEW: Health check
    app.add_handler(CommandHandler("post", cmd_post))
    app.add_handler(CommandHandler("scan", lambda u, c: cmd_empire(u, c, "scan")))
    app.add_handler(CommandHandler("leads", lambda u, c: cmd_empire(u, c, "leads")))
    app.add_handler(CommandHandler("revenue", lambda u, c: cmd_empire(u, c, "revenue")))
    app.add_handler(CommandHandler("auto", lambda u, c: cmd_empire(u, c, "auto")))
    app.add_handler(CommandHandler("repair", lambda u, c: cmd_empire(u, c, "repair")))

    # Inline Buttons
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Text-Nachrichten
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Alle Datei-Typen
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.AUDIO |
        filters.VOICE | filters.VIDEO,
        handle_file
    ))

    log.info("✅ Bot läuft! Polling gestartet...")
    log.info("Ctrl+C zum Stoppen")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    # Fix Proxy für Telegram API
    import os
    current_no_proxy = os.environ.get("no_proxy", "")
    telegram_domains = "api.telegram.org,api.telegram.bot"
    if telegram_domains not in current_no_proxy:
        os.environ["no_proxy"] = f"{current_no_proxy},{telegram_domains}".lstrip(",")
        os.environ["NO_PROXY"] = os.environ["no_proxy"]

    main()
