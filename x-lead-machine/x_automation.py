#!/usr/bin/env python3
"""
X.COM LEAD-MASCHINE
Automatisierte Lead-Generation auf X/Twitter
Maurice's AI Empire
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime

# Config
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
if not MOONSHOT_API_KEY:
    raise ValueError("MOONSHOT_API_KEY environment variable is required. Set it before running this script.")

# Keywords die auf Kaufsignale hindeuten
BUYER_KEYWORDS = [
    "looking for AI",
    "need automation",
    "anyone built",
    "how do I automate",
    "struggling with",
    "hate manual work",
    "need help with",
    "recommend any AI",
    "best tool for",
    "who can help",
    "hiring for AI",
    "budget for automation",
]

# Hashtags zu monitoren
HOT_HASHTAGS = [
    "#AIautomation",
    "#ClaudeCode",
    "#BuildInPublic",
    "#AIAgents",
    "#NoCode",
    "#Automation",
]

# Accounts deren Follower = potenzielle Leads
TARGET_ACCOUNTS = [
    "levelsio",
    "marc_louvion",
    "gregisenberg",
    "taborenz",
    "swyx",
    "alexalbert__",
]

class XLeadMachine:
    """Automatisierte Lead-Generation auf X."""

    def __init__(self):
        self.leads = []
        self.stats = {
            "tweets_analyzed": 0,
            "leads_found": 0,
            "hot_leads": 0,
        }

    async def analyze_tweet_for_lead(self, tweet: dict) -> dict:
        """Analysiere Tweet auf Kaufsignal mit Kimi."""

        prompt = f"""Analysiere diesen Tweet auf Kaufsignale für AI-Automation-Services:

Tweet: {tweet.get('text', '')}
Author: {tweet.get('author', '')}
Engagement: {tweet.get('likes', 0)} likes, {tweet.get('replies', 0)} replies

Bewerte:
1. Kaufsignal (0-10): Hat die Person ein Problem das wir lösen können?
2. Dringlichkeit (0-10): Wie dringend scheint das Bedürfnis?
3. Authority (0-10): Scheint Person Entscheider zu sein?
4. Empfohlene Aktion: (ignore/like/reply/dm)
5. Reply-Vorschlag: Falls reply empfohlen

Antworte als JSON:
{{"score": X, "urgency": X, "authority": X, "action": "...", "reply": "..."}}
"""

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        try:
                            return json.loads(content)
                        except:
                            return {"score": 0, "action": "ignore"}
            except:
                pass
        return {"score": 0, "action": "ignore"}

    async def generate_content(self, topic: str, style: str = "value") -> str:
        """Generiere X-Content mit Kimi."""

        styles = {
            "value": "Gib praktischen Mehrwert, zeige Expertise",
            "controversial": "Sei kontrovers aber backed by facts",
            "behind_scenes": "Zeig was du baust, sei transparent",
            "tutorial": "Schritt-für-Schritt Anleitung",
            "question": "Stelle eine Frage die Engagement erzeugt",
        }

        prompt = f"""Schreibe einen X/Twitter Post zum Thema: {topic}

Stil: {styles.get(style, styles['value'])}

Regeln:
- Max 280 Zeichen (oder Thread-Start)
- Hook in erster Zeile
- Keine Hashtags im Text (die am Ende)
- Kein "Hey" oder "Hallo"
- Direkt zum Punkt
- Call-to-Action am Ende

Beispiel guter Post:
"Ich habe mein ganzes Business automatisiert.

Lead-Gen → AI
Outreach → AI
Follow-ups → AI

Morgen zeig ich euch wie.

Like für Reminder."

Schreibe jetzt den Post:"""

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
            except:
                pass
        return ""

    async def generate_reply(self, original_tweet: str, context: str = "") -> str:
        """Generiere Reply der Mehrwert gibt + Lead nurturet."""

        prompt = f"""Schreibe eine Reply auf diesen Tweet:

Original: {original_tweet}

Kontext: {context}

Ziel: Mehrwert geben + Interesse wecken für AI-Automatisierung

Regeln:
- Max 280 Zeichen
- Nicht salesy
- Echten Mehrwert/Tip geben
- Subtil auf Expertise hinweisen
- Frage stellen um Gespräch zu starten

Schreibe die Reply:"""

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
            except:
                pass
        return ""

    async def generate_dm_sequence(self, lead_info: dict) -> list:
        """Generiere DM-Sequence für Lead."""

        prompt = f"""Erstelle eine 3-DM Sequence für diesen Lead:

Lead Info:
- Name: {lead_info.get('name', 'Unknown')}
- Interesse: {lead_info.get('interest', 'AI Automation')}
- Original Tweet: {lead_info.get('tweet', '')}

Ziel: Termin für 15-Min Discovery Call

DM 1: Erster Kontakt (warm, Bezug auf Tweet)
DM 2: Nach 2 Tagen wenn keine Antwort (mehr Wert geben)
DM 3: Nach 4 Tagen (letzter Versuch, CTA)

Antworte als JSON Array mit 3 DMs:
[{{"day": 0, "message": "..."}}, ...]"""

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "https://api.moonshot.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.6
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        try:
                            return json.loads(content)
                        except:
                            return []
            except:
                pass
        return []

    def get_stats(self) -> dict:
        """Get current stats."""
        return {
            **self.stats,
            "leads": len(self.leads),
            "timestamp": datetime.now().isoformat()
        }


# Content Templates für schnelles Posten
CONTENT_TEMPLATES = {
    "result": """[ERGEBNIS in Zahlen]

Ohne [alte Methode].
Ohne [andere alte Methode].
Nur [deine Methode].

Wollt ihr wissen wie?""",

    "controversial": """Unpopular opinion:

[Kontroverse Aussage]

Hier ist warum:

[3 Punkte als Beweis]""",

    "tutorial": """Wie du [Ergebnis] in [Zeitraum] erreichst 🧵

Schritt 1: [Action]
Schritt 2: [Action]
Schritt 3: [Action]

Ergebnis: [Outcome]

Thread ↓""",

    "question": """Ehrliche Frage an alle [Zielgruppe]:

[Problem-Frage]?

Ich baue gerade [Lösung] und will echte Probleme lösen.

👇""",

    "behind_scenes": """Was ich heute gemacht habe:

- [Task 1]
- [Task 2]
- [Task 3]

Alles automatisiert.
Zeit heute: [X] Minuten.

Das ist der Weg.""",
}


if __name__ == "__main__":
    machine = XLeadMachine()

    print("=" * 50)
    print("X.COM LEAD-MASCHINE")
    print("=" * 50)
    print()
    print("Verfügbare Funktionen:")
    print("1. analyze_tweet_for_lead(tweet) - Tweet auf Kaufsignal prüfen")
    print("2. generate_content(topic, style) - Content generieren")
    print("3. generate_reply(tweet) - Reply generieren")
    print("4. generate_dm_sequence(lead) - DM-Sequence erstellen")
    print()
    print("Content Templates:")
    for name in CONTENT_TEMPLATES:
        print(f"  - {name}")
    print()
    print("Buyer Keywords:", BUYER_KEYWORDS[:5], "...")
    print("Hot Hashtags:", HOT_HASHTAGS)
