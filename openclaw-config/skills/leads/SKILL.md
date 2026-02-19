# SKILL: Leads & CRM
*Lade diesen Skill wenn: Lead, CRM, Sales, Pipeline, DM, Anfrage, BANT, Follow-up, Conversion*

---

## Lead-Maschine Überblick

X/Twitter → Leads → CRM (Port 3500) → Qualifizieren → Verkaufen → Umsatz.
Kein manueller Aufwand nach Setup. Alles automatisiert.

---

## Lead-Quellen

| Quelle | Methode | Priorität |
|--------|---------|-----------|
| X/Twitter Replies | Wer antwortet auf BMA/AI Posts? | HOCH |
| X/Twitter DMs | Wer fragt direkt an? | SEHR HOCH |
| X/Twitter Follows | Wer folgt nach einem Thread? | MITTEL |
| Gumroad Käufer | Wer hat schon gekauft? | SEHR HOCH (upsell) |
| Fiverr Anfragen | Direkte Service-Anfragen | HOCH |

---

## BANT-Qualifizierung

**Jeder Lead bekommt einen Score 0-12:**

### Budget (B) — Kann er bezahlen?
- 1 Punkt: Freelancer/Einzelperson, Budget unklar
- 2 Punkte: KMU, 1-5K EUR Budget wahrscheinlich
- 3 Punkte: Unternehmen, >5K EUR Budget klar

### Authority (A) — Ist er Entscheider?
- 1 Punkt: Recherchiert für jemand anderen
- 2 Punkte: Mitentscheider, muss abstimmen
- 3 Punkte: Alleinentscheider, kann sofort kaufen

### Need (N) — Hat er echten Bedarf?
- 1 Punkt: Vage Interesse
- 2 Punkte: Konkretes Problem benannt
- 3 Punkte: Zeitkritisches Problem, aktiv auf Lösung

### Timeline (T) — Wann will er kaufen?
- 1 Punkt: "Irgendwann"
- 2 Punkte: "In den nächsten 3 Monaten"
- 3 Punkte: "So schnell wie möglich" / "Diese Woche"

### Scoring:
- **9-12:** Hot Lead — sofort bearbeiten, innerhalb 2h antworten
- **6-8:** Warm Lead — nurture, wöchentliche Follow-ups
- **3-5:** Cold Lead — in Content-Funnel, monatliche Touch-Points
- **<3:** Nicht qualifiziert — schließen oder in Newsletter

---

## Lead-Erfassung (CRM Port 3500)

### Beim Erfassen notieren:
```
Name:
Kanal: [X / Fiverr / Gumroad / Direktkontakt]
Datum:
Erste Nachricht: (kurze Zusammenfassung)
BANT-Score: /12
Pipeline-Stufe: [Entdeckt / Qualifiziert / Angebot / Verhandlung / Gewonnen / Verloren]
Nächste Aktion:
Nächstes Datum:
Notizen:
```

### CRM-Befehle:
```bash
python3 empire_engine.py leads  # Leads verarbeiten
# CRM UI: http://localhost:3500
```

---

## Follow-up-System

### Hot Lead (Score 9-12):
- Tag 0: Erste Antwort (< 2 Stunden)
- Tag 1: Follow-up wenn keine Antwort
- Tag 3: Zweiter Follow-up mit konkretem Angebot
- Tag 7: Finaler Follow-up "Ist das noch relevant?"

### Warm Lead (Score 6-8):
- Woche 0: Antwort + Mehrwert-Ressource schicken
- Woche 2: Check-in
- Woche 4: Neues Angebot / Content-Update

### Cold Lead (Score 3-5):
- Monatlicher Newsletter / Update
- Auf gute Posts von ihnen reagieren
- Nach 6 Monaten ohne Reaktion: schließen

---

## Message-Templates

### Erster Kontakt (X Reply):
```
Hey [Name],

[Bezug auf spezifischen Inhalt/Post].
Genau das löse ich mit [Lösung].

Wäre das was für dich?
```

### Qualifizierungs-DM:
```
Hey [Name],

kurze Frage bevor ich dir mehr schicke:
Geht es dir um [Option A] oder [Option B]?

Dann kann ich dir was konkretes empfehlen.

Maurice
```

### Angebot:
```
[Name],

basierend auf dem was du beschrieben hast:
[Konkrete Lösung in 1-2 Sätzen]

Preis: [X] EUR
Timeline: [Y]

Nächster Schritt: kurzes 15min Call?
```

### Follow-up nach Stille:
```
[Name],

melde mich kurz — ist das noch auf deiner Liste
oder hat sich die Priorität geändert?

Kein Druck, nur damit ich weiß ob ich warte.

Maurice
```

---

## Conversion-Optimierung

### Was konvertiert am besten:
1. Spezifischer Bezug auf ihr Problem (kein Copy-Paste)
2. Kleine erste Commitments (kurzes Call vs. großes Angebot)
3. Dringlichkeit durch echte Engpässe (Kapazität, Timing)
4. Social Proof (frühere Kunden, Ergebnisse)

### Was NICHT funktioniert:
- Generische DMs ohne Bezug
- Sofort Preise nennen ohne Qualifizierung
- Zu viel Text in erster Nachricht
- Follow-ups ohne Mehrwert
