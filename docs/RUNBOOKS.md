# 🔧 Runbooks

Standardisierte Vorgehensweisen für häufige Probleme.

## Docker voll → Cleanup

**Symptom:** Festplatte voll, Container starten nicht

```bash
# 1. Gestoppte Container entfernen
docker container prune -f

# 2. Ungenutzte Images entfernen
docker image prune -a -f

# 3. Build-Cache leeren
docker builder prune -f

# 4. Volumes prüfen (vorsichtig!)
docker volume ls
docker volume prune -f
```

## API Error 400 → Router Fix

**Symptom:** Claude/Kimi API gibt 400 zurück

1. API-Key prüfen: `echo $ANTHROPIC_API_KEY | head -c 10`
2. Rate Limits prüfen: Dashboard des Anbieters
3. Request-Format validieren (JSON-Schema)
4. Failover aktivieren: System wechselt automatisch (siehe `claude_failover_system.py`)

## Tokenkosten zu hoch → Budget Regelwerk

**Symptom:** API-Kosten steigen unerwartet

1. Usage-Dashboard prüfen (Anthropic/OpenAI Console)
2. Token-Limits pro Task überprüfen (`atomic-reactor/tasks/`)
3. Modell-Routing anpassen (teure Tasks → günstigeres Modell)
4. Cache-Layer aktivieren (Redis für wiederholte Anfragen)

## CRM startet nicht

**Symptom:** Port 3500 nicht erreichbar

```bash
# 1. Prüfen ob Port belegt
lsof -i :3500

# 2. Dependencies installieren
cd crm && npm install

# 3. Starten
npm start
```

## GitHub Actions fehlgeschlagen

**Symptom:** Workflow rot

1. Actions-Tab → fehlgeschlagener Run öffnen
2. Logs lesen (meist: fehlende Secrets oder Dependency-Problem)
3. Secrets unter Settings → Secrets prüfen
4. Workflow manuell re-triggern
