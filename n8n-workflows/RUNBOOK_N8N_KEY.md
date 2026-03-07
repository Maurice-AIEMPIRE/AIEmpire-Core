# Runbook: n8n API Key — Unblock & Activate

**Status**: LIVE but BLOCKED (Key vorhanden, noch nicht konfiguriert)
**Dauer**: ~5 Minuten
**Risiko**: Niedrig (nur lokale Konfiguration)

---

## 1. Key setzen

Oeffne Terminal und fuege den API Key in deine `.env` Datei ein:

```bash
cd ~/AIEmpire-Core
echo 'N8N_API_KEY=dein_key_hier' >> .env
```

Oder in der n8n Web-UI:
1. Oeffne http://localhost:5678
2. Gehe zu **Settings** → **API**
3. Erstelle einen neuen API Key (falls noch keiner existiert)
4. Kopiere den Key

## 2. Key in Environment laden

```bash
source .env
# Oder manuell:
export N8N_API_KEY="dein_key_hier"
```

Fuer permanente Konfiguration: Key in `~/.zshrc` oder `~/.bashrc` eintragen:
```bash
echo 'export N8N_API_KEY="dein_key_hier"' >> ~/.zshrc
source ~/.zshrc
```

## 3. Testen ob es funktioniert

```bash
python3 n8n-workflows/n8n_connector.py --status
```

**Erwartetes Ergebnis:**
```
  ✅ n8n: UP
  ✅ Ollama: UP
  ✅ OpenClaw: UP (oder DOWN wenn nicht gestartet)
  ✅ Redis: UP (oder DOWN wenn nicht gestartet)
```

Dann Workflows testen:
```bash
python3 n8n-workflows/n8n_connector.py --workflows
```

## 4. Workflows importieren (wenn n8n frisch ist)

```bash
python3 n8n-workflows/n8n_connector.py --import-all
```

Importiert und aktiviert:
- 01_content_engine.json
- 02_ollama_brain.json
- 03_kimi_router.json
- 04_github_monitor.json
- 05_system_health.json
- 06_lead_generator.json

## 5. Rollback (wenn was schiefgeht)

```bash
# Key entfernen:
unset N8N_API_KEY

# Workflows deaktivieren (in n8n Web-UI):
# http://localhost:5678 → jeden Workflow → Toggle auf "Inactive"

# Oder n8n komplett stoppen:
docker stop n8n
# bzw.
pkill -f n8n
```

## 6. Logging

Erfolgreiche Aktivierung hier dokumentieren:
```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) n8n API Key activated, $(python3 n8n-workflows/n8n_connector.py --workflows 2>/dev/null | grep -c '🟢') workflows active" >> ops/logs/n8n_activations.log
```
