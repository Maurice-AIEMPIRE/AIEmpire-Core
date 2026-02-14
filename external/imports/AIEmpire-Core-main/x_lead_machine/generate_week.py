#!/usr/bin/env python3
"""
WOCHEN-CONTENT GENERATOR
Generiert 7 Posts + 1 Thread für die ganze Woche
"""

import asyncio
import aiohttp
import os
from datetime import datetime, timedelta

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")

WEEK_PLAN = [
    {"day": "Montag", "topic": "AI Agents automatisieren mein Business", "style": "result"},
    {"day": "Dienstag", "topic": "Vibe Coding - AI schreibt Code für mich", "style": "tutorial"},
    {"day": "Mittwoch", "topic": "Warum 90% der AI-Berater Faker sind", "style": "controversial"},
    {"day": "Donnerstag", "topic": "Mein AI-Setup heute: 20 Claude Agents", "style": "behind_scenes"},
    {"day": "Freitag", "topic": "Von Elektriker zu AI-Unternehmer", "style": "story"},
    {"day": "Samstag", "topic": "Was ist euer größtes Automatisierungs-Problem?", "style": "question"},
    {"day": "Sonntag", "topic": "Thread: Wie du in 2026 mit AI Geld verdienst", "style": "thread"},
]

STYLES = {
    "result": "Konkretes Ergebnis mit Zahlen zeigen",
    "tutorial": "Praktische Schritt-für-Schritt Anleitung",
    "controversial": "Polarisierende Meinung, aber faktenbasiert",
    "behind_scenes": "Zeig was du gerade baust",
    "story": "Persönliche Geschichte mit Lektion",
    "question": "Echte Frage an die Community",
    "thread": "Ausführlicher Thread mit 7 Posts",
}

async def generate_single_post(topic: str, style: str) -> str:
    """Generiere einen Post."""

    prompt = f"""Schreibe einen X/Twitter Post.

THEMA: {topic}
STIL: {STYLES.get(style, "Mehrwert geben")}

REGELN:
- Max 280 Zeichen
- Deutsche Sprache
- Erste Zeile = Hook
- Keine Hashtags
- Max 1 Emoji
- CTA am Ende
- Kein "Hey/Hallo"

BEISPIEL:
"100 Leads in 24h generiert.

Ohne Ads.
Ohne Cold Calls.
Nur AI.

Like wenn du wissen willst wie."

POST:"""

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
                return data["choices"][0]["message"]["content"]
    return ""


async def generate_thread(topic: str) -> str:
    """Generiere einen 7-teiligen Thread."""

    prompt = f"""Schreibe einen X/Twitter Thread zum Thema: {topic}

FORMAT:
1/7 [Hook mit 🧵]
2/7 [Punkt 1]
3/7 [Punkt 2]
4/7 [Punkt 3]
5/7 [Punkt 4]
6/7 [Punkt 5]
7/7 [CTA: Follow/Like/Retweet]

REGELN:
- Jeder Post max 280 Zeichen
- Auf Deutsch
- Praktischer Mehrwert
- Nummerierung X/7

THREAD:"""

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
                return data["choices"][0]["message"]["content"]
    return ""


async def generate_full_week():
    """Generiere Content für die ganze Woche."""

    print("=" * 60)
    print("📅 WOCHEN-CONTENT GENERATOR")
    print("=" * 60)
    print()

    results = []
    today = datetime.now()

    for i, day in enumerate(WEEK_PLAN):
        date = today + timedelta(days=i)
        print(f"Generiere {day['day']} ({date.strftime('%d.%m.')})...")

        if day["style"] == "thread":
            content = await generate_thread(day["topic"])
        else:
            content = await generate_single_post(day["topic"], day["style"])

        results.append({
            "day": day["day"],
            "date": date.strftime("%Y-%m-%d"),
            "topic": day["topic"],
            "style": day["style"],
            "content": content
        })

        print(f"  ✅ {len(content)} Zeichen")

    # Speichern
    output_file = f"week_content_{today.strftime('%Y%m%d')}.md"

    with open(output_file, "w") as f:
        f.write(f"# X CONTENT WOCHE {today.strftime('%d.%m.%Y')}\n\n")

        for r in results:
            f.write(f"## {r['day']} ({r['date']})\n")
            f.write(f"**Thema:** {r['topic']}\n")
            f.write(f"**Stil:** {r['style']}\n\n")
            f.write("```\n")
            f.write(r["content"])
            f.write("\n```\n\n")
            f.write("---\n\n")

    print()
    print(f"✅ Gespeichert in: {output_file}")
    print()
    print("=" * 60)
    print("VORSCHAU:")
    print("=" * 60)

    for r in results:
        print()
        print(f"📌 {r['day'].upper()} - {r['topic']}")
        print("-" * 40)
        preview = r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"]
        print(preview)

    return results


if __name__ == "__main__":
    asyncio.run(generate_full_week())
