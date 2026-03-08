#!/usr/bin/env python3
"""
GALAXIA BOT - ULTRA-LIGHT (nur stdlib + requests)
Direct Telegram API calls, no dependencies
"""

import json
import os
import time
import logging
from datetime import datetime
from urllib import request, parse
from urllib.error import URLError
import redis
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

if not TOKEN:
    print("❌ BOT_TOKEN not in .env")
    exit(1)

# Connect Redis
try:
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    r.ping()
    logger.info("✅ Redis OK")
except:
    print("❌ Redis connection failed")
    exit(1)

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def send_message(chat_id, text):
    """Send message via Telegram API"""
    params = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    url = f"{BASE_URL}/sendMessage"
    data = parse.urlencode(params).encode('utf-8')
    try:
        req = request.Request(url, data=data)
        with request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except URLError as e:
        logger.error(f"Telegram API error: {e}")
        return None

def get_updates(offset=0):
    """Fetch new messages"""
    url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
    try:
        with request.urlopen(url, timeout=35) as resp:
            return json.loads(resp.read())["result"]
    except:
        return []

def handle_message(chat_id, text, user_id):
    """Process incoming message"""

    # Store in Redis
    msg = {"role": "user", "text": text, "time": datetime.utcnow().isoformat()}
    r.rpush(f"conv:{user_id}", json.dumps(msg))
    r.ltrim(f"conv:{user_id}", -20, -1)

    logger.info(f"📨 User {user_id}: {text[:50]}")

    # Commands
    if text == "/start":
        response = """🌌 **GALAXIA OS BOT**

/status - System
/revenue - Revenue
/evolve - Evolution
/help - Help

DM me anything!"""
    elif text == "/status":
        response = f"""✅ **STATUS**
Redis: Connected ✅
Bot: Running ✅
Time: {datetime.utcnow().strftime('%H:%M:%S')}"""
    elif text == "/revenue":
        response = """💰 **REVENUE**
Gumroad: Ready
Fiverr: Ready
Total: €0"""
    elif text == "/help":
        response = """📖 **/HELP**
/start /status /revenue
/evolve /tasks /logs"""
    elif text.startswith("/evolve"):
        response = "🧬 Evolution started..."
    elif "status" in text.lower():
        response = "System running normally ✅"
    elif "revenue" in text.lower():
        response = "Revenue pipeline ready 💰"
    else:
        response = f"📝 Got: '{text[:30]}...'\n\n(Echo bot active!)"

    # Send response
    msg2 = {"role": "bot", "text": response, "time": datetime.utcnow().isoformat()}
    r.rpush(f"conv:{user_id}", json.dumps(msg2))

    send_message(chat_id, response)

def main():
    offset = 0
    logger.info("🚀 GALAXIA BOT STARTED (Ultra-Light)")
    logger.info(f"Token: {TOKEN[:10]}...")

    while True:
        try:
            updates = get_updates(offset)

            for update in updates:
                update_id = update["update_id"]
                offset = update_id + 1

                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    user_id = msg["from"]["id"]
                    text = msg.get("text", "")

                    if text:
                        handle_message(chat_id, text, user_id)

            if not updates:
                logger.info("⏳ Waiting for messages...")
                time.sleep(2)

        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
