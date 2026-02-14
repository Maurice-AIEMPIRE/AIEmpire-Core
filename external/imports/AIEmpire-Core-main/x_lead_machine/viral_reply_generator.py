#!/usr/bin/env python3
"""
VIRAL REPLY GENERATOR
Generiert Replies auf virale Posts um Leads zu gewinnen
"""

import asyncio
import aiohttp
import os

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")

# Virale Posts zum Replyen (von X gerade)
VIRAL_POSTS = [
    {
        "author": "@milesdeutscher",
        "topic": "30 Automation Ideas",
        "hook": "i dOnT kNoW wHaT tO aUtoMaTe - bro..",
        "content": "30 automation ideas from morning briefings to competitor monitoring"
    },
    {
        "author": "@TheAIColony",
        "topic": "Claude Cowork",
        "hook": "How to Set Up Claude Cowork and Get Real Work Done",
        "content": "Claude working autonomously while you do something else"
    },
    {
        "author": "@pankajkumar_dev",
        "topic": "Claude Opus 4.6 vs GPT-5.3",
        "hook": "The Benchmark Paradox",
        "content": "Claude ships production apps on first try"
    },
    {
        "author": "@tom_doerr",
        "topic": "Memory Agent for AI Tools",
        "hook": "github.com/RedPlanetHQ/core",
        "content": "AI memory persistence across sessions"
    }
]

async def generate_viral_reply(post: dict) -> str:
    """Generiere Reply die Aufmerksamkeit bekommt."""

    prompt = f"""Du antwortest auf einen viralen X/Twitter Post.

ORIGINAL POST:
Author: {post['author']}
Thema: {post['topic']}
Hook: {post['hook']}

ZIEL:
- Mehrwert geben (nicht nur "great post!")
- Eigene Expertise zeigen
- Neugier wecken für DM/Follow

REGELN:
- Max 280 Zeichen
- Deutsch oder Englisch (je nach Post)
- Konkreten Tipp oder Insight geben
- KEIN "Great post!" oder "Love this!"
- Subtil auf eigene Erfahrung verweisen

BEISPIEL guter Reply:
"Number 26 (Personal CRM) changed everything for me.

Built one with Claude in 2 hours.
Now I never forget a follow-up.

Happy to share the template if anyone wants it."

Schreibe jetzt die Reply:"""

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


async def main():
    print("=" * 60)
    print("VIRAL REPLY GENERATOR")
    print("Generiere Replies für aktuelle virale Posts")
    print("=" * 60)
    print()

    for post in VIRAL_POSTS:
        print(f"📝 Reply für {post['author']} - {post['topic']}")
        print("-" * 40)

        reply = await generate_viral_reply(post)
        print(reply)
        print()
        print("=" * 60)
        print()


if __name__ == "__main__":
    asyncio.run(main())
