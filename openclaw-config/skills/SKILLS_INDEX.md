# SKILLS INDEX — Routing-Guide

_Ein Agent. Viele Skills. Voller Kontext. Kein multi-agent Chaos._

Basiert auf dem Ansatz von @jordymaui: Skills > Agents.
Artikel: "You've set up OpenClaw. Now What?"

---

## Warum Skills statt Agents?

| Multi-Agent (alt) | Skills (neu) |
|-------------------|--------------|
| 7+ separate Agents | 1 Agent |
| Context geht bei Handoffs verloren | Context bleibt vollständig erhalten |
| Hunderte EUR/Tag API-Kosten | Flat Rate (Claude Max ~90 EUR/Monat) |
| Debugging = Alptraum | Ein Ort, alles klar |
| Maurice muss Agents managen | Agent managed sich selbst |

---

## Skill-Mapping

### Nach Kanal / Trigger-Wort:

| Kanal / Trigger | Skill laden | Datei |
|-----------------|-------------|-------|
| `#x`, `#twitter`, `post`, `tweet`, `thread`, `viral`, `reply` | X/Twitter | `skills/x/SKILL.md` |
| `#writing`, `schreib`, `text`, `artikel`, `content`, `stimme` | Writing | `skills/writing/SKILL.md` |
| `#bma`, `brandmeldeanlage`, `din 14675`, `wartung`, `esser`, `hekatron` | BMA | `skills/bma/SKILL.md` |
| `#revenue`, `#money`, `umsatz`, `gumroad`, `fiverr`, `pipeline`, `sales` | Revenue | `skills/revenue/SKILL.md` |
| `#dev`, `#code`, `python`, `skill bauen`, `bug`, `script`, `api` | Dev | `skills/dev/SKILL.md` |
| `#leads`, `crm`, `anfrage`, `dm`, `bant`, `follow-up`, `conversion` | Leads | `skills/leads/SKILL.md` |
| `#larry`, `postiz`, `tiktok`, `linkedin`, `scheduling`, `auto-post` | Larry | `skills/larry/SKILL.md` |

### Nach Aufgabentyp:

| Aufgabe | Primärer Skill | Sekundärer Skill |
|---------|----------------|-----------------|
| Tweet schreiben | Writing | X |
| Thread erstellen | X | Writing |
| Lead bearbeiten | Leads | Writing |
| Angebot erstellen | Revenue | Writing |
| BMA-Frage beantworten | BMA | Writing |
| Content planen | Larry | X |
| Code schreiben | Dev | — |
| Neuen Skill bauen | Dev | — |
| Revenue-Review | Revenue | — |

---

## Skill-Kombinations-Regeln

Manche Aufgaben brauchen zwei Skills:

```
Tweet schreiben über BMA-Thema:
  → Writing SKILL laden (Stimme, Regeln)
  → X SKILL laden (Format, Personas)
  → BMA SKILL laden (Fachinhalt)
  → Kombinieren → Post erstellen

Lead-DM schreiben:
  → Leads SKILL laden (BANT, Templates)
  → Writing SKILL laden (Ton, verbotene Wörter)
  → Kombinieren → DM erstellen
```

---

## Cron Jobs → Skills Mapping

Bestehende Jobs verwenden jetzt Skills statt separater Agents:

| Job | Früher (Agent) | Jetzt (Skill) |
|-----|----------------|---------------|
| Daily trends scan | `research` agent | Lade X SKILL → scan routine |
| Daily short-form scripts | `content` agent | Lade X + Writing SKILL |
| Daily offer packaging | `product` agent | Lade Revenue + Writing SKILL |
| Weekly revenue review | `finance` agent | Lade Revenue SKILL |
| Daily content calendar | `content` agent | Lade Larry SKILL |
| YouTube long-form outline | `content` agent | Lade Writing SKILL |
| Daily engagement playbook | `community` agent | Lade X + Leads SKILL |
| Daily KPI snapshot | `analytics` agent | Lade Revenue SKILL |

---

## Neuen Skill hinzufügen

```bash
# 1. Verzeichnis erstellen
mkdir openclaw-config/skills/neuer-skill

# 2. SKILL.md erstellen
touch openclaw-config/skills/neuer-skill/SKILL.md

# 3. In SKILLS_INDEX.md eintragen (diese Datei)

# 4. Agent sagen:
"Install the [neuer-skill] skill"
# oder
"Lade den [neuer-skill] Skill wenn du [trigger] siehst"
```

---

## Aktueller Skill-Status

| Skill | Status | Letzte Änderung |
|-------|--------|-----------------|
| x | ✅ Aktiv | 2026-02-19 |
| writing | ✅ Aktiv | 2026-02-19 |
| bma | ✅ Aktiv | 2026-02-19 |
| revenue | ✅ Aktiv | 2026-02-19 |
| dev | ✅ Aktiv | 2026-02-19 |
| leads | ✅ Aktiv | 2026-02-19 |
| larry | ✅ Aktiv | 2026-02-19 |

---

_Dieser Index wird bei jedem neuen Skill aktualisiert._
_Der Agent liest ihn beim Session-Start um zu wissen welche Skills verfügbar sind._
