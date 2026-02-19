# SKILL: Larry (Social Media Automation)
*Lade diesen Skill wenn: Postiz, TikTok, LinkedIn, Scheduling, Auto-Post, Social Media Automation*

---

## Was Larry macht

Larry ist der Social-Media-Autopilot. Inspiriert von @oliverhenry's Skill der
8 Millionen TikTok-Views in einer Woche gebracht hat.

**Prinzip:** Ein Skill. Ein Agent. Vollautomatische Content-Pipeline.
Content erstellen → planen → posten → analysieren. Ohne Handy anzufassen.

---

## Plattformen

| Plattform | Primärzweck | Posting-Frequenz |
|-----------|-------------|-----------------|
| X/Twitter | Leads, Thought Leadership | 9 Posts/Tag |
| TikTok | Reichweite, Virality | 1-3 Videos/Tag |
| LinkedIn | B2B Leads, Consulting | 1-2 Posts/Tag |
| Instagram | Brand, BMA-Fotos | 1 Post/Tag |

---

## Content-Pipeline

### Schritt 1: Content-Generierung (täglich 09:00)
Basierend auf Trend-Scan vom Vortag:
- 3 kurze Skripte (TikTok/Reel, ≤45 Sek.)
- 9 X/Twitter Posts (fertig zum Posten)
- 2 LinkedIn Artikel (300-500 Wörter)
- 5 Instagram Captions

### Schritt 2: Planung & Scheduling via Postiz
```
Postiz-Verbindung: https://postiz.pro
Authentifizierung: via .env POSTIZ_API_KEY

Zeitplan-Logik:
- X: 07:30, 12:00, 17:30, 21:00 (+ weitere)
- TikTok: 08:00, 18:00
- LinkedIn: 09:00, 14:00
- Instagram: 11:00
```

### Schritt 3: Auto-Post
Postiz übernimmt das Posten — keine manuelle Aktion nötig.
Larry übergibt fertigen Content + Zeitplan.

### Schritt 4: Performance-Analyse (täglich 20:00)
- Welche Posts hatten >500 Impressions?
- Welcher Hook hat am besten funktioniert?
- Was für Content-Format gewinnt diese Woche?
- Anpassung für morgen

---

## Content-Formats die performen

### TikTok / Reels (Skript-Template):
```
[0-3 Sek] HOOK: Schockierende Aussage / Frage / "Das weiß kaum jemand..."
[3-15 Sek] PROBLEM: Was ist das Problem?
[15-35 Sek] LÖSUNG: Die Methode (konkret, Schritte)
[35-42 Sek] BEWEIS: Ergebnis / Zahl / Vorher-Nachher
[42-45 Sek] CTA: "Folge für mehr" oder "Link in Bio"
```

### LinkedIn-Post (Template):
```
[Bold Statement oder Frage]

[Kurze Story oder Kontext - 2-3 Sätze]

Was ich gelernt habe:
• [Punkt 1]
• [Punkt 2]
• [Punkt 3]

[Schlussfrage für Kommentare]

#BMA #AIAutomation #Digitalisierung
```

---

## Postiz-Integration

```python
# Postiz API (via .env POSTIZ_API_KEY)
import aiohttp

async def schedule_post(platform: str, content: str, schedule_time: str):
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "https://postiz.pro/api/v1/posts",
            headers={"Authorization": f"Bearer {config.postiz_api_key}"},
            json={
                "platform": platform,
                "content": content,
                "scheduledFor": schedule_time
            }
        )
    return await response.json()
```

---

## Virality-Trigger

Basierend auf 8M-Views-Learnings:

1. **Spezifische Zahlen** — "8 Millionen in 7 Tagen" > "viele Views"
2. **Kontra-Intuitive Aussagen** — "Mehr Agents = weniger Output"
3. **Persönliche Fehler** — "Ich hab 200 EUR/Tag verbrannt. Dann hab ich das gelernt."
4. **How-To mit Beweis** — nicht nur erklären, zeigen
5. **Timing** — trending Themen binnen 2h aufgreifen

---

## KPIs (wöchentlich)

```
X/Twitter:
- Impressions/Post: Ziel >1.000
- Follower-Growth: Ziel +50/Woche
- Link-Clicks: Ziel >100/Woche

TikTok:
- Views/Video: Ziel >1.000
- Follower-Growth: Ziel +200/Woche

LinkedIn:
- Impressions/Post: Ziel >500
- Anfragen: Ziel 3+/Woche

Instagram:
- Reach/Post: Ziel >300
```

---

## Fehlerbehandlung

Wenn Postiz-API nicht antwortet:
1. Content in `x_lead_machine/queue.md` speichern
2. Nächster Heartbeat-Check: automatisch retry
3. Bei persistentem Fehler: manuell posten + in memory notieren

Niemals Content verlieren — immer zuerst in Queue speichern, dann posten.
