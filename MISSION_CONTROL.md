# Mission Control

## Ziel
Du willst:
- alles verstehen
- mehrere KI-Chats parallel steuern
- Voice als Steuerkanal nutzen
- aus Prinzipien echte Umsatz-Ausfuehrung machen

Dieses Setup liefert genau das als Betriebssystem.

## Start in 10 Minuten
1. `python3 -m automation.mission_control status`
2. `python3 -m automation.mission_control plan`
3. `python3 -m automation.mission_control multi-chat --prompt "Baue 5 neue Offer-Angles" --agents 9`
4. `python3 -m automation.mission_control revenue-add --amount 0 --source "baseline" --note "Startpunkt"`

Optional mit Sprache:
1. Audio aufnehmen (z.B. `command.m4a`)
2. `python3 -m automation.mission_control voice --audio command.m4a --dispatch`

## Bedienlogik
- `status`: zeigt Lage, Ziel-Luecke und Aktivitaet.
- `plan`: macht aus Umsatzziel einen 7-Tage-Umsetzungsplan.
- `multi-chat`: startet viele KI-Agenten parallel ueber Router-Modelle.
- `voice`: transkribiert, erkennt Intent, kann automatisch ausfuehren.
- `revenue-add`: macht Fortschritt messbar.

## Legion 50 (dein 50-Agenten-Team)
Du fuehrst ein 50er-Team als Mastermind-System mit klarer Kommando-Struktur.

Doktrin:
- `ai-vault/AGENT_LEGION_50_DOCTRINE.md`

Schnellstart:
1. Dry-Run (ohne API-Kosten):
   - `./automation/scripts/run_legion_50.sh`
2. Live-Run (echte Ausfuehrung):
   - `./automation/scripts/run_legion_50.sh --execute`
3. Eigener Fokus-Prompt:
   - `./automation/scripts/run_legion_50.sh --execute --prompt "Baue 3 neue Angebote und 30 Content-Assets fuer diese Woche."`

Hinweis:
- Das Script startet 5 Wellen mit je 10 Agenten. Das ist stabiler als 50 auf einmal.
- Fuer maximale Geschwindigkeit kannst du `--tier premium` setzen.

## Think and Grow Rich -> operative Uebersetzung
Die 13 Prinzipien sind nicht als Motivation gespeichert, sondern als:
- taegliche Aktion
- woechentlicher Kontrollpunkt

Quelle:
- `automation/config/mission_control.json` -> `think_and_grow_rich_execution`

Damit wird aus Theorie:
- klares Tagesziel
- taegliche Sales-Execution
- laufende Entscheidungsklarheit
- messbare Persistenz

## Wichtiger Rahmen
Kein System kann Einkommen garantieren. Dieses Setup maximiert Ausfuehrungsqualitaet, Geschwindigkeit und Konsistenz. Ergebnis kommt aus sauberer taeglicher Umsetzung.
