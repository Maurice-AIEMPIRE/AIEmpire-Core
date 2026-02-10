#!/usr/bin/env python3
"""
TIKTOK FACTORY - Massenhaft TikTok Scripts generieren.
Bewaehrtes 45-Sekunden Format: Hook → Problem → Story → Steps → CTA.

Nutzt Ollama (kostenlos) fuer Generierung.
Output: Markdown-Dateien + JSON Queue fuer Content Machine.

Usage:
    python tiktok_factory.py                   # Status
    python tiktok_factory.py --generate 20     # 20 Scripts generieren
    python tiktok_factory.py --niche bma_ai    # Nische waehlen
    python tiktok_factory.py --series 5        # 5-teilige Serie
    python tiktok_factory.py --export          # Alle Scripts als Markdown
"""

import asyncio
import argparse
import json
import os
import sys
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

import logging

log = logging.getLogger(__name__)

try:
    from ollama_engine import OllamaEngine, LLMResponse
except Exception as e:
    OllamaEngine = None
    LLMResponse = None
    log.exception("ollama_engine import failed: %s", e)

STATE_DIR = Path(__file__).parent / "state"
TIKTOK_DIR = STATE_DIR / "tiktok"
SCRIPTS_FILE = TIKTOK_DIR / "all_scripts.json"

# ── TikTok Niches + Hooks ────────────────────────────────────

TIKTOK_NICHES = {
    "geld_verdienen": {
        "name": "Geld verdienen mit AI",
        "target": "18-35, Side Hustler, Anfaenger",
        "hooks": [
            "Kopiere diesen Prompt - verdiene damit.",
            "Dieses AI-Tool macht dir Geld im Schlaf.",
            "500 EUR mit einem einzigen Prompt.",
            "ChatGPT kann dir Geld verdienen. So gehts.",
            "3 AI Side Hustles die JETZT funktionieren.",
            "Dein erster Euro mit AI. Heute noch.",
            "Stop scrolling. Dieser Trick bringt dir Geld.",
            "Die meisten nutzen ChatGPT falsch. Hier ist die richtige Methode.",
            "Ich habe 1000 EUR verdient. Ohne Code. Ohne Team.",
            "Dieses Gumroad-Produkt hat sich von alleine gebaut.",
            "5 Minuten Setup. Passives Einkommen. Hier ist wie.",
            "Warum verkaufen alle Prompts? Weil es funktioniert.",
        ],
        "topics": [
            "Digitale Produkte auf Gumroad mit AI erstellen",
            "Fiverr Gigs mit AI automatisieren",
            "AI-generierte E-Books verkaufen",
            "Prompt-Pakete verkaufen auf Gumroad",
            "Freelancing mit Claude Code",
            "AI Thumbnails und Grafiken verkaufen",
            "Newsletter mit AI starten und monetarisieren",
            "Social Media Management mit AI als Service",
            "AI Consulting fuer kleine Unternehmen",
            "Automatisierte Lead-Generierung als Dienstleistung",
        ],
    },
    "ai_automation": {
        "name": "AI Automation",
        "target": "25-45, Unternehmer, Freelancer",
        "hooks": [
            "Ich habe mein ganzes Business automatisiert.",
            "50.000 AI Agents arbeiten fuer mich.",
            "Warum machst du das noch manuell?",
            "Dieses Tool spart dir 10 Stunden pro Woche.",
            "AI ersetzt keine Jobs. AI ersetzt LANGSAME Leute.",
            "Mein Morgen: Kaffee. Laptop. Alles laeuft schon.",
            "In 2 Stunden was andere in 2 Wochen schaffen.",
            "Du brauchst kein Team. Du brauchst AI Agents.",
            "Automatisierung ist kein Luxus. Es ist Pflicht.",
            "Mein CRM fuellt sich von alleine. Hier ist wie.",
        ],
        "topics": [
            "n8n Workflows fuer Anfaenger - automatisiere alles",
            "Claude Code: Von der Idee zum fertigen Tool in 1 Stunde",
            "AI Agents die deine Emails beantworten",
            "Automatische Lead-Generierung mit AI",
            "CRM das sich selbst fuellt - so baust du es",
            "Ollama: Kostenlose AI auf deinem Computer",
            "5 Business-Prozesse die AI sofort uebernehmen kann",
            "AI Meeting Notes die sich selbst schreiben",
            "Competitor Monitoring mit AI - automatisch",
            "Rechnungen die sich selbst erstellen",
        ],
    },
    "bma_ai": {
        "name": "BMA + AI (Brandmeldeanlagen)",
        "target": "25-55, Errichter, Planer, Facility Manager",
        "hooks": [
            "16 Jahre BMA-Erfahrung. Jetzt macht es AI.",
            "Dein Wartungsprotokoll in 5 Minuten statt 5 Stunden.",
            "DIN 14675 auf Knopfdruck.",
            "Brandmeldeanlagen + AI = die Zukunft.",
            "Esser, Hekatron, Siemens - AI kennt alle.",
            "Dokumentation die sich selbst schreibt.",
            "Der groesste Pain bei BMA? Papierkram. Geloest.",
            "Fachkraeftemangel in der BMA-Branche? AI ist die Antwort.",
        ],
        "topics": [
            "BMA-Wartungsprotokoll mit AI generieren",
            "DIN 14675 Checkliste automatisiert",
            "Stoerungsanalyse mit AI - schneller als jeder Techniker",
            "BMA-Dokumentation die sich selbst schreibt",
            "Revisionssichere Protokolle mit AI erstellen",
            "Fachkraeftemangel loesen mit AI-Assistenz",
            "BMA-Planung beschleunigen mit Claude Code",
            "Wartungsintervalle optimieren mit Datenanalyse",
        ],
    },
    "build_in_public": {
        "name": "Build in Public Journey",
        "target": "20-40, Indie Hacker, Creator, Developer",
        "hooks": [
            "Tag {day}: AI Empire aufbauen.",
            "Von 0 auf 100k. Alles dokumentiert.",
            "Mein Revenue Dashboard. Komplett offen.",
            "Fehler Nummer {n}. Das habe ich gelernt.",
            "Was ich diese Woche verdient habe. Ehrlich.",
            "Die Wahrheit ueber AI-Businesses.",
            "Niemand zeigt dir die Fails. Ich schon.",
            "Mein Stack. Meine Kosten. Alles transparent.",
        ],
        "topics": [
            "Woche 1: Erste Schritte zum AI Business",
            "Mein kompletter Tech-Stack (und was es kostet)",
            "Der groesste Fehler den Anfaenger machen",
            "Von der Idee zum ersten zahlenden Kunden",
            "Wie ich meinen ersten Gumroad Sale bekommen habe",
            "24 Stunden Challenge: AI Business von 0 aufbauen",
            "Meine Revenue-Zahlen - komplett transparent",
            "Was funktioniert hat und was nicht",
        ],
    },
}

# ── Series Templates ─────────────────────────────────────────

SERIES_TEMPLATES = [
    {
        "name": "5 AI Side Hustles",
        "parts": 5,
        "structure": "Jeder Teil = 1 konkreter Side Hustle mit Schritt-fuer-Schritt",
    },
    {
        "name": "7 Tage AI Challenge",
        "parts": 7,
        "structure": "Tag 1-7, jeden Tag eine Aufgabe, am Ende: funktionierendes AI Business",
    },
    {
        "name": "3 Tools die dein Leben veraendern",
        "parts": 3,
        "structure": "Tool 1: Ollama (gratis AI), Tool 2: Claude Code (vibe coding), Tool 3: n8n (automation)",
    },
    {
        "name": "Von 0 auf 1000 EUR",
        "parts": 5,
        "structure": "Schritt 1: Nische, Schritt 2: Produkt, Schritt 3: Plattform, Schritt 4: Content, Schritt 5: Skalieren",
    },
    {
        "name": "BMA Basics",
        "parts": 5,
        "structure": "Grundlagen der Brandmeldetechnik fuer Nicht-Techniker, einfach erklaert",
    },
]


class TikTokFactory:
    """Massenhaft TikTok Scripts generieren mit Ollama."""

    def __init__(self):
        TIKTOK_DIR.mkdir(parents=True, exist_ok=True)
        if OllamaEngine is not None:
            self.ollama = OllamaEngine()
        else:
            self.ollama = None
            log.warning("OllamaEngine not available - TikTokFactory limited")
        self.scripts = self._load_scripts()
        self._stats = {
            "total_generated": len(self.scripts),
            "by_niche": {},
            "series_created": 0,
        }

    def _load_scripts(self) -> list:
        if SCRIPTS_FILE.exists():
            try:
                return json.loads(SCRIPTS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save_scripts(self):
        SCRIPTS_FILE.write_text(json.dumps(self.scripts, indent=2, ensure_ascii=False))

    async def generate_script(
        self,
        niche: str = "geld_verdienen",
        custom_topic: str = "",
        custom_hook: str = "",
    ) -> dict:
        """Generiert ein einzelnes TikTok Script."""
        niche_data = TIKTOK_NICHES.get(niche, TIKTOK_NICHES["geld_verdienen"])
        hook = custom_hook or random.choice(niche_data["hooks"])
        topic = custom_topic or random.choice(niche_data["topics"])

        # Template-Variablen ersetzen
        hook = hook.replace("{day}", str(random.randint(1, 365)))
        hook = hook.replace("{n}", str(random.randint(1, 50)))

        prompt = f"""Schreibe ein TikTok-Video-Script. Genau 45 Sekunden lang.

THEMA: {topic}
ZIELGRUPPE: {niche_data['target']}

SCHREIBE GENAU IN DIESEM FORMAT:
Hook (0-2s): [Scroll-Stopper Satz, max 10 Woerter, macht neugierig]
Problem (2-7s): [Zeige das Problem der Zielgruppe, relatable, emotional]
Mini-Story (7-20s): [Konkretes Beispiel oder Demo, mit Zahlen/Beweis]
3 Steps (20-35s): Schritt 1 - [Konkrete Aktion]. Schritt 2 - [Konkrete Aktion]. Schritt 3 - [Konkrete Aktion].
CTA (35-45s): [Klarer CTA: Follow fuer mehr / Link in Bio / Kommentar]
Caption: [Max 100 Zeichen, catchy, mit 1 Emoji]
Hashtags: [5-7 Hashtags mit #]

HOOK INSPIRATION: "{hook}"

REGELN:
1. Einfache Sprache - ein 15-Jaehriger muss es verstehen
2. Konkrete Zahlen (EUR, Minuten, Schritte)
3. Jeder Schritt SOFORT umsetzbar
4. Deutsch
5. KEIN Bullshit, KEIN Hype ohne Substanz
6. Kurze Saetze

Schreibe das komplette Script:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available", "niche": niche}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=800,
        )

        if response.success:
            script = {
                "id": len(self.scripts) + 1,
                "platform": "tiktok",
                "niche": niche,
                "topic": topic,
                "hook_inspiration": hook,
                "content": response.content.strip(),
                "model": response.model,
                "tokens": response.tokens,
                "duration_ms": response.duration_ms,
                "created_at": datetime.now().isoformat(),
                "status": "ready",
            }
            self.scripts.append(script)
            self._save_scripts()
            self._stats["total_generated"] += 1
            self._stats["by_niche"][niche] = self._stats["by_niche"].get(niche, 0) + 1
            return script
        else:
            return {"error": response.error, "niche": niche}

    async def generate_batch(self, count: int = 20, niche: str = "") -> list:
        """Batch-Generierung von TikTok Scripts."""
        print(f"\n  TIKTOK FACTORY: Generiere {count} Scripts")
        if niche:
            print(f"  Nische: {niche}")
        print()

        results = []
        start = time.time()

        for i in range(count):
            n = niche or random.choice(list(TIKTOK_NICHES.keys()))
            print(f"\r    [{i+1}/{count}] {n}...", end="", flush=True)

            try:
                script = await self.generate_script(niche=n)
                results.append(script)
                if "error" not in script:
                    print(f"\r    [{i+1}/{count}] {n} - OK ({script.get('tokens', 0)} tokens)", flush=True)
                else:
                    print(f"\r    [{i+1}/{count}] {n} - ERROR: {script['error'][:50]}", flush=True)
            except Exception as e:
                results.append({"error": str(e), "niche": n})
                print(f"\r    [{i+1}/{count}] {n} - EXCEPTION: {str(e)[:50]}", flush=True)

        elapsed = time.time() - start
        ok = len([r for r in results if "error" not in r])
        print(f"\n    Fertig! {ok}/{count} erfolgreich in {elapsed:.1f}s")
        return results

    async def generate_series(
        self,
        series_idx: int = 0,
        niche: str = "geld_verdienen",
    ) -> list:
        """Generiert eine zusammenhaengende TikTok-Serie."""
        template = SERIES_TEMPLATES[series_idx % len(SERIES_TEMPLATES)]
        print(f"\n  TIKTOK SERIE: {template['name']} ({template['parts']} Teile)")

        results = []
        for part in range(1, template["parts"] + 1):
            topic = f"{template['name']} - Teil {part}/{template['parts']}: {template['structure']}"
            hook = f"Teil {part} von {template['parts']}: {template['name']}"

            print(f"    Teil {part}/{template['parts']}...")
            script = await self.generate_script(
                niche=niche,
                custom_topic=topic,
                custom_hook=hook,
            )

            if "error" not in script:
                script["series"] = template["name"]
                script["part"] = part
                script["total_parts"] = template["parts"]
            results.append(script)

        self._stats["series_created"] += 1
        ok = len([r for r in results if "error" not in r])
        print(f"\n    Serie fertig! {ok}/{template['parts']} Teile erfolgreich")
        return results

    def export_all(self, niche: str = "", limit: int = 50) -> str:
        """Exportiert Scripts als Markdown."""
        scripts = self.scripts
        if niche:
            scripts = [s for s in scripts if s.get("niche") == niche]
        scripts = scripts[-limit:]

        if not scripts:
            return "Keine TikTok Scripts vorhanden."

        lines = [
            f"# TIKTOK SCRIPTS - {datetime.now().strftime('%Y-%m-%d')}",
            f"Total: {len(scripts)} Scripts",
            "",
        ]

        for s in scripts:
            lines.extend([
                f"## Script #{s.get('id', '?')} - {s.get('niche', '?')}",
                f"Topic: {s.get('topic', '?')}",
                f"Status: {s.get('status', '?')}",
                "",
                "```",
                s.get("content", ""),
                "```",
                "",
                "---",
                "",
            ])

        return "\n".join(lines)

    def show_status(self):
        """Zeigt Factory Status."""
        by_niche = {}
        for s in self.scripts:
            n = s.get("niche", "unknown")
            by_niche[n] = by_niche.get(n, 0) + 1

        ready = sum(1 for s in self.scripts if s.get("status") == "ready")
        posted = sum(1 for s in self.scripts if s.get("status") == "posted")

        print(f"""
{'='*60}
  TIKTOK FACTORY - Status
{'='*60}

  SCRIPTS:
    Total:            {len(self.scripts)}
    Ready:            {ready}
    Posted:           {posted}

  BY NICHE:""")
        for niche, count in sorted(by_niche.items(), key=lambda x: x[1], reverse=True):
            print(f"    {niche:<20s}: {count}")

        print(f"""
  AVAILABLE NICHES:
    {', '.join(TIKTOK_NICHES.keys())}

  SERIES TEMPLATES:""")
        for i, t in enumerate(SERIES_TEMPLATES):
            print(f"    [{i}] {t['name']} ({t['parts']} Teile)")

        print(f"""
  COMMANDS:
    python tiktok_factory.py --generate 20
    python tiktok_factory.py --generate 20 --niche bma_ai
    python tiktok_factory.py --series 0
    python tiktok_factory.py --export
{'='*60}""")


async def main():
    parser = argparse.ArgumentParser(description="TikTok Factory")
    parser.add_argument("--generate", type=int, metavar="N", help="N Scripts generieren")
    parser.add_argument("--niche", type=str, default="", help="Nische waehlen")
    parser.add_argument("--series", type=int, metavar="IDX", help="Serie generieren (Index)")
    parser.add_argument("--export", action="store_true", help="Alle Scripts exportieren")
    args = parser.parse_args()

    factory = TikTokFactory()

    if args.generate:
        await factory.generate_batch(count=args.generate, niche=args.niche)
    elif args.series is not None:
        await factory.generate_series(series_idx=args.series, niche=args.niche or "geld_verdienen")
    elif args.export:
        md = factory.export_all(niche=args.niche)
        print(md)
    else:
        factory.show_status()


if __name__ == "__main__":
    asyncio.run(main())
