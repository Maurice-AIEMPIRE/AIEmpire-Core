# Claude Limit Watch

Dieses Paket enthaelt:
- `claude_watch/CLAUDE_PROMPT.md` fuer dein High-Think Claude Setup (inkl. Handoff-Block)
- `claude_watch/RESUME_TEMPLATE.md` fuer saubere Resume-Nachrichten
- `claude_watch/claude_limit_watch.py` fuer Live-Monitoring der Usage-Limits (Web, Countdown, API)

## Schnellstart (Web-UI Monitoring)
1. Playwright installieren.
```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```
2. Watcher starten.
```bash
python3 claude_watch/claude_limit_watch.py web --pause-for-login --interval 30
```
3. Im geoeffneten Browser einloggen und die Limits-Seite offen lassen.

Wenn das Limit von 100 Prozent auf frei wechselt, bekommst du eine macOS Notification.

## Countdown-Variante (ohne Browser)
Falls du die Reset-Timer kennst, kannst du sie angeben:
```bash
python3 claude_watch/claude_limit_watch.py countdown --reset-in 2h32m --reset-in 1h32m
```

## API-Variante (Anthropic API)
Damit ueberwachst du API-Limits (nicht die Claude-Web-Planlimits).
```bash
export ANTHROPIC_API_KEY="sk-..."
export ANTHROPIC_MODEL="claude-3-5-sonnet-latest"
python3 claude_watch/claude_limit_watch.py api --interval 60
```

## Automatisch etwas starten, wenn Limits frei sind
Nutze `--on-ready` fuer ein Kommando, das bei Freigabe ausgefuehrt wird.
```bash
python3 claude_watch/claude_limit_watch.py web --pause-for-login --on-ready "open -a 'Google Chrome'"
```

## Sprache und Erkennung anpassen
Standard ist `--language auto` (Deutsch + Englisch). Du kannst eigene Phrasen hinzufuegen:
```bash
python3 claude_watch/claude_limit_watch.py web --phrase "limit erreicht" --phrase "usage cap"
```
Oder einen eigenen Regex fuer Prozent-Erkennung:
```bash
python3 claude_watch/claude_limit_watch.py web --percent-regex "(\\d{1,3})\\s*%\\s*(used|verwendet)"
```

## Hinweise
- Der Watcher sucht nach "100% used" oder "100 % verwendet" sowie "limit reached".
- Wenn du eine andere Sprache nutzt, sag mir kurz Bescheid, dann passe ich die Erkennung an.
