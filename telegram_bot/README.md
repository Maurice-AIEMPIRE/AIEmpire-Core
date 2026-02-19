# Empire Telegram Bot + Terminus Fix

## Telegram Bot — Steuere dein Empire vom Handy

### Quick Start (1 Befehl auf dem Mac)

```bash
bash telegram_bot/setup_telegram_bot.sh
```

### Was der Bot kann

| Befehl | Funktion |
|--------|----------|
| `/status` | System-Status (Ollama, RAM, CPU) |
| `/revenue` | Umsatz-Report |
| `/scan` | News + Trends scannen |
| `/auto` | Voller autonomer Zyklus |
| `/models` | Ollama Modelle anzeigen |
| `/ip` | Mac IP-Adressen |
| `/ssh` | SSH Verbindungs-Info |
| `/repair` | Auto-Repair ausfuehren |
| `!befehl` | Shell-Befehl auf Mac |
| `$scan` | Empire Engine Befehl |
| `?frage` | AI fragen (Ollama/Kimi) |
| Einfach tippen | AI Chat |

### Beispiele in Telegram

```
/status              → Systemstatus
!git status          → Git auf dem Mac
!ollama list         → Welche Modelle laufen
$revenue             → Umsatz-Report
?Was ist DIN 14675   → AI fragt Ollama
Schreib mir einen viralen Post → AI generiert Content
```

## Terminus Fix — SSH auf Mac

```bash
bash telegram_bot/fix_terminus.sh
```

### Haeufige Probleme

| Problem | Loesung |
|---------|---------|
| Connection refused | SSH aktivieren: `sudo systemsetup -setremotelogin on` |
| Connection timed out | Gleiches WLAN? Mac IP pruefen |
| Permission denied | Mac-Login-Passwort verwenden |
| Von unterwegs | Tailscale installieren |
