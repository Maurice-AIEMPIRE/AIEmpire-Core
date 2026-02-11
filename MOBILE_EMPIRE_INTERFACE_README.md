# Mobile Empire Interface

Eine Web-App für den Zugriff auf Gemini, Grok und Claude von deinem Handy aus.

## Setup

1. **API Keys setzen:**
   ```bash
   export GEMINI_API_KEY="dein_google_gemini_api_key"
   export CLAUDE_API_KEY="dein_anthropic_claude_api_key"
   export GROK_API_KEY="dein_xai_grok_api_key"
   ```

2. **Starten:**
   ```bash
   ./start_mobile_interface.sh
   ```

3. **Von Handy zugreifen:**
   - Öffne deinen Browser auf dem Handy
   - Gehe zu: `http://[ip-deines-computers]:8000`
   - Zum Beispiel: `http://192.168.1.100:8000`

## Features

- **Chat mit AI-Modellen:** Gemini, Claude Haiku, Grok Fastmode
- **Code-Generierung:** Erstelle Code in verschiedenen Sprachen
- **Mobile-optimiert:** Responsive Design für Smartphones
- **Real-time Chat:** Sofortige Antworten

## API Keys bekommen

### Gemini (Google)
1. Gehe zu [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Erstelle einen API Key
3. Setze `GEMINI_API_KEY`

### Claude (Anthropic)
1. Gehe zu [Anthropic Console](https://console.anthropic.com/)
2. Erstelle einen API Key
3. Setze `CLAUDE_API_KEY`

### Grok (xAI)
1. Grok ist bereits integriert (simuliert)
2. Optional: Setze `GROK_API_KEY` für echte API

## Sicherheit

- Die App läuft lokal auf deinem Computer
- API Keys werden nur lokal verwendet
- Keine Daten werden an externe Server gesendet (außer zu den AI-APIs)

## Troubleshooting

- **Port 8000 belegt:** Ändere den Port in `mobile_empire_interface.py`
- **API Fehler:** Überprüfe deine API Keys
- **Netzwerk:** Stelle sicher, dass dein Handy im gleichen WLAN ist