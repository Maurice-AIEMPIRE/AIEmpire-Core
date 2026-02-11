# AI Pruef-Prompts fuer BMA-Abnahmen
## Copy-Paste Prompts fuer ChatGPT / Claude / Gemini

**Anleitung:** Kopiere den Prompt, fuege deine Daten ein, erhalte sofort Ergebnis.

---

## Prompt 1: Abnahme-Protokoll generieren

```
Du bist ein erfahrener BMA-Fachplaner nach DIN 14675.

Erstelle ein Abnahmeprotokoll fuer folgende Brandmeldeanlage:

PROJEKTDATEN:
- Objekt: [OBJEKT NAME]
- Adresse: [ADRESSE]
- Errichter: [FIRMA]
- BMZ-Typ: [HERSTELLER/MODELL]
- Anzahl Melder: [ANZAHL]
- Meldertypen: [RAUCH/WAERME/MULTI/HAND]
- Abnahmedatum: [DATUM]

ERGEBNISSE:
- Maengel Kategorie A: [ANZAHL oder KEINE]
- Maengel Kategorie B: [ANZAHL oder KEINE]
- Maengel Kategorie C: [ANZAHL oder KEINE]
- Besondere Feststellungen: [TEXT]

Erstelle ein vollstaendiges, professionelles Abnahmeprotokoll im deutschen
Fachjargon. Struktur: Kopfdaten, Pruefumfang, Ergebnisse, Maengelliste,
Gesamtbewertung, Empfehlungen.
```

---

## Prompt 2: Maengel-Analyse und Priorisierung

```
Ich habe bei einer BMA-Abnahme folgende Maengel festgestellt:

[LISTE DEINE MAENGEL HIER AUF - z.B.:
- Rauchmelder in Raum 203 fehlt
- Handfeuermelder Flur EG Montagehoehe 1,6m statt 1,4m
- Brandschutzklappe Kanal K12 keine Ansteuerung
- Laufkarte Bereich 3 nicht aktuell]

Kategorisiere jeden Mangel:
- Kategorie A: Sicherheitsrelevant (sofort beheben)
- Kategorie B: Funktionsrelevant (vor Inbetriebnahme)
- Kategorie C: Dokumentation (innerhalb 30 Tage)

Fuer jeden Mangel:
1. Kategorie mit Begruendung
2. Normverweis (DIN 14675 / VDE 0833)
3. Behebungsvorschlag
4. Geschaetzter Aufwand
5. Empfohlene Frist
```

---

## Prompt 3: Checkliste Vollstaendigkeit pruefen

```
Pruefe ob meine BMA-Abnahme-Checkliste alle relevanten Punkte abdeckt.

Meine geprueften Punkte:
[KOPIERE DEINE LISTE HIER]

Vergleiche mit den Anforderungen aus:
- DIN 14675 (Brandmeldeanlagen - Aufbau und Betrieb)
- DIN VDE 0833-1 (Gefahrenmeldeanlagen - Allgemeine Festlegungen)
- DIN VDE 0833-2 (Brandmeldeanlagen)
- Landesbauordnung Brandschutz

Was fehlt? Was wurde uebersehen?
Erstelle eine Liste der fehlenden Pruefpunkte mit Normverweis.
```

---

## Prompt 4: Wartungsprotokoll erstellen

```
Erstelle ein Wartungsprotokoll fuer eine BMA-Anlage.

ANLAGENDATEN:
- Anlage: [BMZ HERSTELLER/MODELL]
- Standort: [GEBAEUDE]
- Letzte Wartung: [DATUM]
- Wartungsintervall: [QUARTALSWEISE/HALBJAEHRLICH]

DURCHGEFUEHRTE ARBEITEN:
[LISTE DEINE ARBEITEN - z.B.:
- Funktionspruefung 15 Rauchmelder (Pruefgas)
- Akku-Messung: 12,4V / 7Ah
- Revision Handfeuermelder EG
- Pruefung UE zur Leitstelle]

FESTGESTELLTE MAENGEL:
[MAENGEL ODER "KEINE"]

Erstelle ein professionelles Wartungsprotokoll mit:
- Kopfdaten
- Arbeiten mit Ergebnis
- Messwerte
- Maengel und Empfehlungen
- Naechster Wartungstermin
```

---

## Prompt 5: Angebot fuer BMA-Projekt erstellen

```
Erstelle ein professionelles Angebot fuer folgendes BMA-Projekt:

PROJEKT:
- Art: [NEUANLAGE / ERWEITERUNG / SANIERUNG]
- Objekt: [GEBAEUDE-TYP und GROESSE]
- Geschosse: [ANZAHL]
- Raeume mit Meldern: ca. [ANZAHL]
- Besonderheiten: [z.B. Tiefgarage, Serverraum, Kueche]

LEISTUNGSUMFANG:
[STICHPUNKTE - z.B.:
- BMZ mit 4 Linien
- 120 Rauchmelder
- 15 Handfeuermelder
- Aufschaltung Feuerwehr
- Ansteuerung 8 Brandschutzklappen
- Inbetriebnahme und Abnahme]

Erstelle ein Angebot mit:
- Positionsnummern
- Einzelpreisen (realistische Marktpreise Deutschland 2026)
- Materialliste
- Montageaufwand
- Inbetriebnahme
- Gesamtsumme netto/brutto
```

---

## Prompt 6: Schulungsunterlage fuer Betreiber

```
Erstelle eine Kurzanleitung fuer den Betreiber einer Brandmeldeanlage.

ANLAGE:
- BMZ: [HERSTELLER/MODELL]
- Standort: [GEBAEUDE]

Die Anleitung soll enthalten:
1. Was tun bei ALARM? (Schritt fuer Schritt)
2. Was tun bei STOERUNG? (Schritt fuer Schritt)
3. Was tun bei ABSCHALTUNG?
4. Wie wird die Anlage zurueckgesetzt?
5. Wen anrufen im Notfall? (Platzhalter fuer Nummern)
6. Was NICHT tun (haeufige Fehler)

Sprache: Einfach, verstaendlich, auch fuer Nicht-Techniker.
Format: Kann ausgedruckt und neben der BMZ aufgehaengt werden.
Maximal 2 Seiten.
```

---

## Prompt 7: DIN-Normen Quick-Check

```
Ich plane eine Brandmeldeanlage fuer:
- Gebaeude: [TYP - z.B. Buerogebaeude, Krankenhaus, Hotel, Lager]
- Flaeche: [QM]
- Geschosse: [ANZAHL]
- Nutzung: [BESCHREIBUNG]
- Bundesland: [BUNDESLAND]

Welche Normen und Vorschriften muss ich beachten?
Erstelle eine Checkliste mit:
1. Relevante DIN-Normen
2. Landesbauordnung Besonderheiten
3. Meldertyp-Empfehlung pro Bereich
4. Ueberwachungsumfang (Voll/Teilschutz)
5. Besondere Anforderungen fuer diesen Gebaeudetyp
```

---

*AI Pruef-Prompts v1.0 - (c) Maurice Pfeifer / AI Empire*
*Einfach kopieren, Daten einfuegen, professionelles Ergebnis erhalten.*
