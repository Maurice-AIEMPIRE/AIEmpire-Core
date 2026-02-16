#!/usr/bin/env python3
"""
HOOK GENERATOR - Larry-Style virale Hooks fuer YouTube Shorts.

Hook-Formel (Larry-Prinzip):
  [Andere Person] + [Konflikt/Zweifel] → "ich hab's gezeigt" → Reaktion/Payoff

Templates sind maschinenlesbar + menschlich editierbar.
Agent lernt welche Hook-Typen performen (via memory/performance.jsonl).
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional

# ── Hook Templates (Larry-Style) ─────────────────────────

HOOK_TEMPLATES = {
    # ── Conflict + Reveal ────────────────────────────
    "OTHER_PERSON_CONFLICT_REVEAL": {
        "name": "Andere Person + Konflikt + Enthuellung",
        "beschreibung": "Jemand zweifelt/blockt → du zeigst es → Payoff",
        "formel": "[Person] [Zweifel] ... [Beweis/Enthuellung]",
        "templates": [
            "Mein {person} meinte, {zweifel}... dann hab ich ihm {beweis} gezeigt.",
            "{person} hat gelacht als ich {aktion}... {wochen} spaeter {ergebnis}.",
            "Alle sagten {zweifel}. Keiner glaubt was dann passiert ist.",
            "Mein {person} wollte {zweifel}... bis ich {beweis} vorgelegt hab.",
            "{person} meinte: '{zweifel_quote}' - 30 Tage spaeter: {ergebnis}.",
        ],
        "variablen": {
            "person": ["Chef", "Kollege", "Kunde", "Partner", "Mentor", "Freund"],
            "zweifel": [
                "das funktioniert nie", "das ist Zeitverschwendung",
                "AI ersetzt keine echten Experten", "damit verdient man kein Geld",
                "das ist zu kompliziert", "der Markt ist gesaettigt",
            ],
            "beweis": [
                "die Zahlen", "den ersten Auftrag", "das Dashboard",
                "den Kontoauszug", "das Ergebnis", "die Automatisierung",
            ],
            "ergebnis": [
                "5-stellig im Monat", "er wollte mitmachen",
                "komplett automatisiert", "3x mehr Auftraege",
                "er hat selbst angefangen", "Revenue verdoppelt",
            ],
        },
        "viral_score": 9,
    },

    "IMPOSSIBLE_THEN_PROOF": {
        "name": "Unmoeglich... bis jetzt",
        "beschreibung": "Etwas galt als unmoeglich → dann Beweis",
        "formel": "[Unmoeglich-Claim] → [Beweis dagegen]",
        "templates": [
            "Ich dachte {unmoeglich}... bis ich {entdeckung} gefunden hab.",
            "Das sollte {unmoeglich} sein. Hier ist der Beweis.",
            "Jeder sagt {unmoeglich}. Hier sind meine {beweis_typ}.",
            "{unmoeglich}? Schau dir das an.",
        ],
        "variablen": {
            "unmoeglich": [
                "AI kann keine kreativen Texte", "ohne Budget kein Business",
                "Automation ist nur fuer Konzerne", "faceless Content geht nicht viral",
                "man braucht ein Team", "das dauert Jahre",
            ],
            "entdeckung": [
                "dieses Tool", "diese Methode", "diesen Workflow",
                "dieses System", "diese Strategie",
            ],
            "beweis_typ": [
                "Ergebnisse", "Zahlen", "Screenshots", "Resultate",
            ],
        },
        "viral_score": 8,
    },

    "SECRET_REVEAL": {
        "name": "Geheimnis Enthuellung",
        "beschreibung": "Insider-Wissen das 'die meisten nicht kennen'",
        "formel": "[X% kennen das nicht] → [Geheimnis]",
        "templates": [
            "99% der {zielgruppe} wissen nicht, dass {geheimnis}.",
            "Das verraet dir niemand ueber {thema}.",
            "Die {zielgruppe} die {erfolg} haben, machen alle {geheimnis}.",
            "Ich hab {zeitraum} gebraucht um das zu verstehen: {geheimnis}.",
        ],
        "variablen": {
            "zielgruppe": [
                "Unternehmer", "Freelancer", "Content Creator",
                "Handwerker", "Selbststaendigen", "Startups",
            ],
            "geheimnis": [
                "AI kann 90% der Arbeit uebernehmen",
                "du brauchst nur 3 Systeme", "der Markt ist riesig",
                "Automation kostet fast nichts", "ein einziges Tool reicht",
            ],
            "thema": [
                "AI Automation", "Content Marketing", "Lead Generation",
                "passive Einnahmen", "Skalierung", "Faceless Content",
            ],
        },
        "viral_score": 8,
    },

    "MISTAKE_WARNING": {
        "name": "Fehler-Warnung",
        "beschreibung": "Harter Fehler + Warnung + Loesung",
        "formel": "[Fehler den alle machen] → [Konsequenz] → [Loesung]",
        "templates": [
            "STOP! Wenn du {fehler}, verlierst du {konsequenz}.",
            "Der groesste Fehler bei {thema}: {fehler}.",
            "Ich hab {verlust} verloren weil ich {fehler}. Mach das nicht.",
            "3 Fehler die dein {thema} killen - Nummer 2 ist fatal.",
        ],
        "variablen": {
            "fehler": [
                "ohne System arbeitest", "alles manuell machst",
                "keine Automation nutzt", "auf Perfektion wartest",
                "nicht trackst", "keinen Funnel hast",
            ],
            "konsequenz": [
                "tausende Euro", "Monate an Zeit", "alle deine Leads",
                "dein ganzes Business", "den Vorsprung",
            ],
            "thema": [
                "AI Business", "Content Strategie", "Lead Generation",
                "YouTube Shorts", "Automation", "Freelancing",
            ],
        },
        "viral_score": 7,
    },

    "STEP_BY_STEP": {
        "name": "Schritt-fuer-Schritt Anleitung",
        "beschreibung": "Konkreter Nutzen in X einfachen Schritten",
        "formel": "[Ergebnis] in [Anzahl] Schritten",
        "templates": [
            "So {ergebnis} in {anzahl} Schritten:",
            "{anzahl} Schritte zu {ergebnis} (kostenlos):",
            "Wie ich {ergebnis} - {anzahl} Schritte, jeder kann das:",
            "{ergebnis}? {anzahl} Schritte. Fertig.",
        ],
        "variablen": {
            "ergebnis": [
                "automatisierst du dein Business",
                "generierst du 100 Leads/Tag",
                "erstellst du viralen Content",
                "baust du passive Einnahmen auf",
                "verdienst du mit AI Geld",
            ],
            "anzahl": ["3", "5", "7"],
        },
        "viral_score": 7,
    },

    "CONTRARIAN_TAKE": {
        "name": "Kontroverse Meinung",
        "beschreibung": "Gegen den Mainstream → Aufmerksamkeit",
        "formel": "[Mainstream-Meinung] ist FALSCH. Hier ist warum.",
        "templates": [
            "Unpopular Opinion: {mainstream} ist komplett falsch.",
            "Alle reden ueber {mainstream}. Keiner checkt {wahrheit}.",
            "{mainstream}? Das ist der groesste Mythos in {branche}.",
            "Hot Take: {wahrheit}. Und ja, ich meine das ernst.",
        ],
        "variablen": {
            "mainstream": [
                "du brauchst Social Media Praesenz",
                "mehr Content = mehr Erfolg",
                "AI nimmt dir deinen Job weg",
                "Freelancer verdienen wenig",
            ],
            "wahrheit": [
                "ein System schlaegt 1000 Posts",
                "Automation ist der einzige Hebel",
                "AI macht dich 10x produktiver",
                "ein guter Funnel reicht",
            ],
            "branche": ["AI", "Marketing", "Business", "Content"],
        },
        "viral_score": 9,
    },
}


# ── Hook Generator ───────────────────────────────────────

class HookGenerator:
    """Generiert virale Hooks nach Larry-Formel."""

    def __init__(self, channel_dir: Optional[Path] = None):
        self.templates = dict(HOOK_TEMPLATES)
        self.channel_dir = channel_dir

        # Lade Channel-spezifische Hook-Templates
        if channel_dir:
            custom_file = channel_dir / "skills" / "hooks.json"
            if custom_file.exists():
                try:
                    custom = json.loads(custom_file.read_text())
                    self.templates.update(custom)
                except (json.JSONDecodeError, OSError):
                    pass

        # Performance-Gewichte (lernt aus Memory)
        self._weights = {k: v["viral_score"] for k, v in self.templates.items()}
        self._load_performance_weights()

    def _load_performance_weights(self):
        """Laedt Performance-Daten aus Channel Memory."""
        if not self.channel_dir:
            return
        perf_file = self.channel_dir / "memory" / "performance.jsonl"
        if not perf_file.exists():
            return
        try:
            hook_scores = {}
            with open(perf_file, "r") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    hook_type = entry.get("hook_template", "")
                    views = entry.get("views", 0)
                    if hook_type and hook_type in self.templates:
                        if hook_type not in hook_scores:
                            hook_scores[hook_type] = []
                        hook_scores[hook_type].append(views)

            # Update Gewichte basierend auf Performance
            for hook_type, view_list in hook_scores.items():
                if len(view_list) >= 3:
                    avg_views = sum(view_list) / len(view_list)
                    # Normalisiere: mehr Views = hoeheres Gewicht
                    self._weights[hook_type] = min(10, max(1, avg_views / 1000))
        except (json.JSONDecodeError, OSError):
            pass

    def generate(self, template_key: Optional[str] = None,
                 niche: str = "ai_automation",
                 count: int = 1) -> List[Dict]:
        """Generiert Hook(s)."""
        results = []
        for _ in range(count):
            # Template waehlen (gewichtet nach Performance)
            if template_key and template_key in self.templates:
                key = template_key
            else:
                key = self._weighted_choice()

            template = self.templates[key]
            hook_text = self._fill_template(template)

            results.append({
                "hook_template": key,
                "hook_text": hook_text,
                "template_name": template["name"],
                "viral_score": template["viral_score"],
                "performance_weight": self._weights.get(key, 5),
            })

        return results

    def _weighted_choice(self) -> str:
        """Waehlt Template gewichtet nach Performance."""
        keys = list(self._weights.keys())
        weights = [self._weights[k] for k in keys]
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0
        for key, weight in zip(keys, weights):
            cumulative += weight
            if r <= cumulative:
                return key
        return keys[0]

    def _fill_template(self, template: Dict) -> str:
        """Fuellt ein Template mit zufaelligen Variablen."""
        templates_list = template.get("templates", [])
        if not templates_list:
            return ""

        text = random.choice(templates_list)
        variablen = template.get("variablen", {})

        for var_name, var_options in variablen.items():
            placeholder = "{" + var_name + "}"
            if placeholder in text:
                text = text.replace(placeholder, random.choice(var_options), 1)

        # Nicht ausgefuellte Placeholders entfernen
        import re
        text = re.sub(r'\{[a-z_]+\}', '...', text)

        return text

    def generate_variants(self, topic: str, count: int = 3) -> List[Dict]:
        """Generiert mehrere Hook-Varianten fuer A/B Testing."""
        variants = []
        used_templates = set()

        for _ in range(count):
            # Verschiedene Templates verwenden
            available = [k for k in self.templates if k not in used_templates]
            if not available:
                available = list(self.templates.keys())

            key = random.choice(available)
            used_templates.add(key)

            hooks = self.generate(template_key=key)
            if hooks:
                hook = hooks[0]
                hook["variant_id"] = len(variants)
                hook["topic"] = topic
                variants.append(hook)

        return variants

    def get_template_stats(self) -> List[Dict]:
        """Gibt alle Templates mit ihren Gewichten zurueck."""
        stats = []
        for key, template in self.templates.items():
            stats.append({
                "key": key,
                "name": template["name"],
                "base_viral_score": template["viral_score"],
                "performance_weight": self._weights.get(key, 5),
                "template_count": len(template.get("templates", [])),
            })
        stats.sort(key=lambda x: x["performance_weight"], reverse=True)
        return stats

    def export_hooks_md(self) -> str:
        """Exportiert alle Hooks als Markdown (fuer skills/hooks.md)."""
        lines = ["# Hook Templates - Larry-Style\n"]
        for key, template in self.templates.items():
            lines.append(f"## {template['name']}")
            lines.append(f"**Key:** `{key}`")
            lines.append(f"**Viral Score:** {template['viral_score']}/10")
            lines.append(f"**Formel:** {template.get('formel', '-')}")
            lines.append(f"**Beschreibung:** {template['beschreibung']}")
            lines.append("\n**Templates:**")
            for t in template.get("templates", []):
                lines.append(f"- `{t}`")
            lines.append("")
        return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hook Generator - Larry-Style")
    parser.add_argument("--generate", type=int, default=0, help="X Hooks generieren")
    parser.add_argument("--variants", type=str, default="", help="A/B Varianten fuer Topic")
    parser.add_argument("--stats", action="store_true", help="Template-Stats anzeigen")
    parser.add_argument("--export", action="store_true", help="Als Markdown exportieren")
    args = parser.parse_args()

    gen = HookGenerator()

    if args.generate > 0:
        hooks = gen.generate(count=args.generate)
        for h in hooks:
            print(f"  [{h['viral_score']}/10] {h['template_name']}")
            print(f"    > {h['hook_text']}")
            print()
    elif args.variants:
        variants = gen.generate_variants(args.variants)
        print(f"\n  A/B HOOK VARIANTEN fuer: {args.variants}\n")
        for v in variants:
            print(f"  Variante {v['variant_id']+1} [{v['viral_score']}/10] {v['template_name']}")
            print(f"    > {v['hook_text']}")
            print()
    elif args.stats:
        print(f"\n{'='*60}")
        print(f"  HOOK TEMPLATE STATS")
        print(f"{'='*60}")
        for s in gen.get_template_stats():
            print(f"  {s['name']:<35s} Score: {s['base_viral_score']}/10  "
                  f"Weight: {s['performance_weight']:.1f}  "
                  f"Templates: {s['template_count']}")
        print(f"{'='*60}\n")
    elif args.export:
        print(gen.export_hooks_md())
    else:
        # Default: 5 Hooks generieren
        print(f"\n{'='*60}")
        print(f"  HOOK GENERATOR - Larry-Style")
        print(f"  {len(HOOK_TEMPLATES)} Templates, virale Hooks")
        print(f"{'='*60}\n")
        hooks = gen.generate(count=5)
        for h in hooks:
            print(f"  [{h['viral_score']}/10] {h['template_name']}")
            print(f"    > {h['hook_text']}")
            print()


if __name__ == "__main__":
    main()
