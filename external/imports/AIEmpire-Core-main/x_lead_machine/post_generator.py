#!/usr/bin/env python3
"""
X POST GENERATOR - Kimi-powered Content
Generiert virale Posts basierend auf Trends
"""

import asyncio
import aiohttp
import os
from datetime import datetime

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")

# Aktuelle Trends Februar 2026
TRENDS = [
    "Claude Code und AI Agents",
    "Vibe Coding - AI schreibt den Code",
    "MCP Model Context Protocol",
    "50.000 AI Agents gleichzeitig",
    "Von 0 auf €100k mit AI",
    "Ollama - kostenlose lokale LLMs",
    "AI Automation Agency starten",
    "ChatGPT vs Claude vs Gemini",
    "Build in Public Journey",
    "No-Code AI Automation",
]

# Post-Stile
STYLES = {
    "result": "Zeige ein konkretes Ergebnis mit Zahlen. Hook → Ergebnis → Wie → CTA",
    "controversial": "Kontroverse Meinung die Diskussion startet. Polarisierend aber faktenbasiert",
    "tutorial": "Schritt-für-Schritt Anleitung. Nummeriert, praktisch umsetzbar",
    "question": "Engagement-Frage an die Community. Echt interessiert, nicht fake",
    "behind_scenes": "Zeig was du gerade baust/machst. Transparent, authentisch",
    "story": "Kurze Story mit Lektion. Problem → Lösung → Learning",
}

async def generate_post(topic: str, style: str = "result") -> dict:
    """Generiere einen X-Post mit Kimi."""

    style_desc = STYLES.get(style, STYLES["result"])

    prompt = f"""Du bist ein X/Twitter Ghostwriter für einen AI-Automation-Experten.

THEMA: {topic}
STIL: {style_desc}

REGELN:
1. Max 280 Zeichen (oder sage "THREAD" wenn länger)
2. Erste Zeile = Hook (stoppt Scroll)
3. Keine Hashtags im Text
4. Kein "Hey" oder "Hallo"
5. Keine Emojis außer maximal 1-2
6. Call-to-Action am Ende
7. Schreibe auf Deutsch

BEISPIEL (result style):
"Von 0 auf 100 Leads in 24 Stunden.

Ohne Cold Calls.
Ohne Ads.
Ohne Team.

Nur AI + Strategie.

Like wenn du wissen willst wie."

Generiere jetzt den Post:"""

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.moonshot.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8
            }
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "topic": topic,
                    "style": style,
                    "post": content,
                    "generated_at": datetime.now().isoformat()
                }
            else:
                return {"error": f"API Error: {resp.status}"}


async def generate_thread(topic: str, points: int = 7) -> list:
    """Generiere einen Thread mit mehreren Posts."""

    prompt = f"""Schreibe einen X/Twitter Thread zum Thema: {topic}

REGELN:
1. {points} Posts (nummeriert 1/{points} etc.)
2. Post 1 = Hook mit "🧵" am Ende
3. Jeder Post max 280 Zeichen
4. Praktischer Mehrwert
5. Letzter Post = CTA (Follow, Like, Retweet)
6. Auf Deutsch

FORMAT:
1/{points}
[Hook Post]

2/{points}
[Content]

...

{points}/{points}
[CTA]

Schreibe den Thread:"""

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.moonshot.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshot-v1-32k",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "topic": topic,
                    "thread": content,
                    "posts": points,
                    "generated_at": datetime.now().isoformat()
                }
            else:
                return {"error": f"API Error: {resp.status}"}


async def generate_week_content() -> list:
    """Generiere Content für eine ganze Woche."""

    week_plan = [
        {"day": "Montag", "topic": TRENDS[0], "style": "result"},
        {"day": "Dienstag", "topic": TRENDS[1], "style": "tutorial"},
        {"day": "Mittwoch", "topic": TRENDS[2], "style": "controversial"},
        {"day": "Donnerstag", "topic": TRENDS[3], "style": "behind_scenes"},
        {"day": "Freitag", "topic": TRENDS[4], "style": "story"},
        {"day": "Samstag", "topic": TRENDS[5], "style": "question"},
        {"day": "Sonntag", "topic": TRENDS[6], "style": "result"},
    ]

    results = []
    for day in week_plan:
        post = await generate_post(day["topic"], day["style"])
        post["day"] = day["day"]
        results.append(post)
        print(f"✅ {day['day']}: {day['topic'][:30]}...")

    return results


async def main():
    print("=" * 50)
    print("X POST GENERATOR - Kimi Powered")
    print("=" * 50)
    print()

    # Generiere einen Beispiel-Post
    print("Generiere Beispiel-Post...")
    post = await generate_post("Claude Code AI Agents", "result")

    if "error" not in post:
        print()
        print("📝 GENERIERTER POST:")
        print("-" * 40)
        print(post["post"])
        print("-" * 40)
        print()
        print(f"Topic: {post['topic']}")
        print(f"Style: {post['style']}")
    else:
        print(f"❌ Error: {post['error']}")

    print()
    print("VERFÜGBARE FUNKTIONEN:")
    print("- generate_post(topic, style) - Einzelner Post")
    print("- generate_thread(topic, points) - Thread")
    print("- generate_week_content() - Ganze Woche")
    print()
    print("STYLES:", list(STYLES.keys()))
    print("TRENDS:", [t[:20]+"..." for t in TRENDS[:5]])


if __name__ == "__main__":
    asyncio.run(main())
