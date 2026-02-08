# 🔒 Security Playbook

Regeln und Prozesse für sichere Entwicklung im AI Empire.

## Secret Handling

### Regeln

1. **Niemals** Secrets in Code committen
2. **Immer** `.env` in `.gitignore` (ist bereits konfiguriert)
3. **Immer** `.env.example` als Template pflegen (ohne echte Werte)
4. In CI/CD: GitHub Secrets verwenden (`Settings → Secrets → Actions`)

### Benötigte Secrets

| Secret | Verwendet in | Beschreibung |
|--------|-------------|--------------|
| `ANTHROPIC_API_KEY` | Claude Failover, Issue Bot | Claude API Zugang |
| `MOONSHOT_API_KEY` | Issue Bot, Content Gen | Kimi/Moonshot API |
| `OPENAI_API_KEY` | Optional | ChatGPT Fallback |
| `GITHUB_TOKEN` | Automatisch | GitHub Actions Token |

### Secret Rotation

- API-Keys alle 90 Tage rotieren
- Nach jedem Leak sofort rotieren
- Alte Keys sofort deaktivieren

## .env Regeln

```bash
# Richtig ✅
cp .env.example .env
# Werte eintragen
nano .env

# Falsch ❌
git add .env
```

## Minimal Permissions

- GitHub Token: Nur benötigte Scopes
- API Keys: Nur benötigte Endpoints
- Docker: Keine `--privileged` Container
- Dateisystem: Keine `777` Berechtigungen

## Dependency Security

- Regelmäßig `pip audit` und `npm audit` ausführen
- Dependabot-Alerts im Repository aktivieren
- Keine ungepinnten Dependencies in Produktion

## Incident Response

1. **Erkennen:** Alert oder manuelle Entdeckung
2. **Isolieren:** Betroffenen Service stoppen
3. **Beheben:** Fix implementieren und testen
4. **Dokumentieren:** Post-Mortem in `/docs`
5. **Verbessern:** Prävention einbauen
