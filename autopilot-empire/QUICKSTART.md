# ═══════════════════════════════════════════════════════════════
# AUTOPILOT EMPIRE - Schnellstart Anleitung
# Maurice's AI Business System
# ═══════════════════════════════════════════════════════════════

## 🚀 30-Sekunden Start

```bash
cd autopilot-empire
bash start.sh
```

Das war's! System läuft.

---

## 📋 Detaillierte Anleitung

### Schritt 1: Voraussetzungen prüfen

**Erforderlich:**
- Mac Mini M4 (oder kompatibel)
- Docker Desktop installiert
- 16+ GB RAM
- 50+ GB freier Speicher (für AI Models)

**Prüfen:**
```bash
docker --version          # Docker muss installiert sein
docker-compose --version  # Docker Compose auch
```

### Schritt 2: Projekt starten

```bash
# In das Projekt-Verzeichnis wechseln
cd ~/AIEmpire-Core/autopilot-empire

# Automatischer Start
bash start.sh
```

**Was passiert:**
1. `.env` wird erstellt (falls nicht vorhanden)
2. Docker Services starten (Ollama, PostgreSQL, Redis, etc.)
3. Health Checks laufen automatisch
4. System ist bereit in ~30 Sekunden

### Schritt 3: AI-Modelle herunterladen (nur beim ersten Start)

```bash
# Dauert ~20 Minuten
bash download-models.sh
```

**Heruntergeladene Modelle:**
- mixtral-8x7b (7.3 GB) - Strategic Decisions
- llama3.3 (4.9 GB) - General Tasks
- qwen2.5 (3.8 GB) - Content Creation
- deepseek-coder (3.4 GB) - Code Generation  
- openhermes (2.9 GB) - Error Recovery
- neural-chat (2.7 GB) - Monitoring

**Total: ~25 GB**

### Schritt 4: Dashboards öffnen

```bash
# Agent Dashboard
open http://localhost:8000

# Monitoring Dashboard
open http://localhost:9090
```

### Schritt 5: System überwachen

```bash
# Service Status
docker-compose ps

# Live Logs
docker-compose logs -f orchestrator

# Nur Errors
docker-compose logs --tail=50 orchestrator | grep ERROR
```

---

## 📱 iPhone Remote Access (Optional)

### Setup (einmalig auf Mac)

```bash
bash iphone-remote-setup.sh
```

### iPhone Apps installieren

1. **Tailscale** (App Store) - VPN für sicheren Zugriff
2. **Termius** (App Store) - SSH Client

### iPhone verbinden

**Tailscale:**
1. App öffnen
2. Mit gleichem Account wie Mac anmelden
3. Verbindung herstellen

**Termius:**
1. "New Host" erstellen
2. Hostname: [Tailscale IP vom Setup-Script]
3. Username: [dein Mac-Username]
4. Password: [dein Mac-Passwort]
5. Verbinden

**Im Safari:**
- Dashboard: `http://[Tailscale-IP]:8000`
- Monitoring: `http://[Tailscale-IP]:9090`

---

## 🔧 Konfiguration

### API Keys hinzufügen (optional)

```bash
# .env bearbeiten
nano .env

# Diese Zeilen editieren:
OPENROUTER_API_KEY=sk-or-v1-...    # Für Premium Models
ANTHROPIC_API_KEY=sk-ant-...       # Für Claude
OPENAI_API_KEY=sk-...              # Für GPT-4
```

### Targets anpassen

```bash
# In .env
REVENUE_TARGET=100.0               # Tägliches Ziel (EUR)
TARGET_TIKTOK_DAILY=30.0          # TikTok Ziel
TARGET_FIVERR_DAILY=70.0          # Fiverr Ziel
```

---

## 🛠 Häufige Befehle

```bash
# System starten
docker-compose up -d

# System stoppen
docker-compose down

# System neu starten
docker-compose restart

# Alle Logs
docker-compose logs -f

# Nur ein Service
docker-compose logs -f orchestrator

# Service Status
docker-compose ps

# In Container einsteigen
docker exec -it autopilot-orchestrator bash

# Database öffnen
docker exec -it autopilot-db psql -U autopilot

# Redis CLI
docker exec -it autopilot-redis redis-cli

# Health Check
curl http://localhost:8000/health
curl http://localhost:9090/health
```

---

## 🧪 Tests ausführen

```bash
# Health Checks
python test_health.py

# Oder mit Docker
docker-compose exec orchestrator python test_health.py
```

---

## 📊 Revenue verfolgen

### Via Dashboard
- http://localhost:8000 → Stats ansehen

### Via API
```bash
# Heutige Revenue
curl http://localhost:8000/stats

# Breakdown nach Source
curl http://localhost:8000/revenue/breakdown

# Tägliche Historie
curl http://localhost:8000/revenue/daily
```

### Via Database
```bash
docker exec -it autopilot-db psql -U autopilot

# In psql:
SELECT * FROM daily_revenue_v ORDER BY date DESC LIMIT 7;
SELECT * FROM agent_performance_v;
SELECT * FROM content_performance_v;
```

---

## 🔍 Troubleshooting

### Problem: Services starten nicht

```bash
# Logs prüfen
docker-compose logs

# Einzelnen Service neu starten
docker-compose restart orchestrator

# Alles neu bauen
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Problem: Ollama Models nicht gefunden

```bash
# Models manuell herunterladen
bash download-models.sh

# Oder einzeln
docker exec -it autopilot-ollama ollama pull mixtral:8x7b
```

### Problem: Port bereits belegt

```bash
# Andere Ports in docker-compose.yml verwenden
# z.B. Zeile 48: "8001:8000" statt "8000:8000"

nano docker-compose.yml
# Dann neu starten
docker-compose down && docker-compose up -d
```

### Problem: Database Connection Error

```bash
# Database Status
docker-compose ps postgres-master

# Database Logs
docker-compose logs postgres-master

# Database neu initialisieren (⚠️ löscht alle Daten!)
docker-compose down -v
docker-compose up -d
```

---

## 📈 Performance Optimierung

### Mehr CPU für Ollama

```yaml
# In docker-compose.yml unter ollama-master:
deploy:
  resources:
    limits:
      cpus: '8'      # Mehr CPUs
      memory: 32G    # Mehr RAM
```

### Mehr Orchestrator Workers

```yaml
# In docker-compose.yml unter orchestrator:
deploy:
  replicas: 3  # 3 Orchestrator Instances
```

### Faster Model Loading

```bash
# Models im RAM halten
OLLAMA_KEEP_ALIVE=24h docker-compose up -d
```

---

## 🔐 Security Checklist

- [ ] `.env` nie committen
- [ ] Starke Passwörter in Production
- [ ] Firewall konfiguriert
- [ ] Tailscale für Remote Access
- [ ] Regelmäßige Backups von `data/`
- [ ] API Keys sicher aufbewahren

---

## 💾 Backup & Restore

### Backup erstellen

```bash
# Alles stoppen
docker-compose down

# Data Ordner sichern
tar -czf autopilot-backup-$(date +%Y%m%d).tar.gz data/

# Wieder starten
docker-compose up -d
```

### Restore

```bash
# Stoppen
docker-compose down

# Backup entpacken
tar -xzf autopilot-backup-YYYYMMDD.tar.gz

# Starten
docker-compose up -d
```

---

## 🎓 Nächste Schritte

1. ✅ System läuft - Dashboard checken
2. ⏳ Modelle laden (~20 Min)
3. 📊 Erste Logs beobachten
4. 📱 iPhone Setup (optional)
5. 💰 Erste Revenue Events warten
6. 📈 Performance analysieren
7. 🚀 Skalieren!

---

## 🆘 Support

**Logs prüfen:**
```bash
docker-compose logs -f
```

**Health prüfen:**
```bash
python test_health.py
```

**GitHub Issues:**
Falls Probleme auftreten, Issue erstellen mit:
- Fehlermeldung
- Docker Logs
- System Info (OS, Docker Version)

---

**Happy Building! 🚀**
