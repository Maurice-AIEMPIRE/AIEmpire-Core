# Docker Troubleshooting Guide

> Die 50 haeufigsten Docker-Probleme geloest – Spare Stunden beim Debugging.

**Preis: EUR 99 | Format: PDF | Sofort-Download**

---

## Kapitel 1: Top 50 Docker Fehler + Loesungen

### Kategorie 1: Container starten nicht (Fehler 1-15)

**1. "docker: Cannot connect to the Docker daemon"**
```bash
# Ursache: Docker Daemon laeuft nicht
# Loesung:
sudo systemctl start docker          # Linux
open -a Docker                        # Mac
# Windows: Docker Desktop neu starten
```

**2. "port is already allocated"**
```bash
# Ursache: Port wird bereits genutzt
# Loesung:
lsof -i :PORT_NUMMER                  # Prozess finden
kill -9 PID                           # Prozess beenden
# Oder anderen Port nutzen:
docker run -p 3501:3500 mein-image
```

**3. "OCI runtime create failed"**
```bash
# Ursache: Meist Architektur-Mismatch (ARM vs x86)
# Loesung:
docker run --platform linux/amd64 mein-image
# Oder Multi-Arch Build:
docker buildx build --platform linux/amd64,linux/arm64 -t mein-image .
```

**4. "no space left on device"**
```bash
# Ursache: Docker verbraucht zu viel Speicher
# Loesung:
docker system prune -a                # ALLES aufraemen
docker volume prune                   # Ungenutzte Volumes
docker image prune -a                 # Ungenutzte Images
df -h                                 # Speicher pruefen
```

**5. "exec format error"**
```bash
# Ursache: Binary-Architektur passt nicht
# Loesung auf Apple Silicon:
docker run --platform linux/amd64 mein-image
# Oder: Image fuer ARM64 neu bauen
```

**6. "container is unhealthy"**
```bash
# Ursache: Health Check schlaegt fehl
# Loesung:
docker inspect --format='{{.State.Health}}' container-name
docker logs container-name            # Logs pruefen
# Health Check anpassen:
HEALTHCHECK --interval=30s --timeout=10s --retries=5 \
  CMD curl -f http://localhost:3000/ || exit 1
```

**7. "bind mount source path does not exist"**
```bash
# Ursache: Lokaler Pfad existiert nicht
# Loesung:
mkdir -p /pfad/zum/verzeichnis
docker run -v /pfad/zum/verzeichnis:/app/data mein-image
```

**8. "network not found"**
```bash
# Ursache: Docker Network existiert nicht
# Loesung:
docker network create mein-netzwerk
docker run --network mein-netzwerk mein-image
```

**9. "permission denied" beim Starten**
```bash
# Ursache: Keine Docker-Berechtigung
# Loesung (Linux):
sudo usermod -aG docker $USER
newgrp docker
# Danach: Ausloggen und wieder einloggen
```

**10. "image not found"**
```bash
# Ursache: Image existiert nicht oder Name falsch
# Loesung:
docker search mein-image              # Suchen
docker pull mein-image:latest         # Explizit pullen
docker images                         # Lokale Images pruefen
```

**11. "COPY failed: file not found"**
```bash
# Ursache: Datei nicht im Build-Context
# Loesung:
# Pruefen: .dockerignore schliesst die Datei aus?
cat .dockerignore
# Build-Context pruefen:
docker build --no-cache -t test .
```

**12. "cannot start service: Mounts denied"**
```bash
# Ursache: Docker Desktop File Sharing nicht konfiguriert
# Loesung (Mac/Windows):
# Docker Desktop → Settings → Resources → File Sharing
# Pfad hinzufuegen
```

**13. "ContainerConfig: no such file or directory"**
```bash
# Ursache: Korrupter Container
# Loesung:
docker rm -f container-name
docker rmi image-name
docker build -t image-name .
```

**14. "error creating overlay mount"**
```bash
# Ursache: Korruptes Storage Backend
# Loesung:
sudo systemctl stop docker
sudo rm -rf /var/lib/docker/overlay2
sudo systemctl start docker
```

**15. "DNS resolution failed"**
```bash
# Ursache: Container hat keinen DNS-Zugang
# Loesung:
docker run --dns 8.8.8.8 mein-image
# Oder in daemon.json:
echo '{"dns": ["8.8.8.8", "8.8.4.4"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

### Kategorie 2: Build-Probleme (Fehler 16-25)

**16. "COPY --from stage not found"**
```bash
# Ursache: Multi-Stage Build Fehler
# Loesung: Stage-Name pruefen
FROM node:22 AS builder    # <-- AS name definieren
COPY --from=builder /app/dist ./dist  # <-- Name nutzen
```

**17. "npm install" haengt im Build**
```bash
# Loesung: --production Flag + Cache optimieren
RUN npm ci --production --ignore-scripts
# Oder mit timeout:
RUN timeout 120 npm install || npm install
```

**18. Layer Cache nicht genutzt**
```bash
# Best Practice: Package files VOR Source Code kopieren
COPY package*.json ./
RUN npm ci
COPY . .           # Source Code kommt NACH npm ci
```

**19. Image zu gross**
```bash
# Loesung: Alpine + Multi-Stage
FROM node:22-alpine AS builder
RUN npm ci && npm run build

FROM node:22-alpine
COPY --from=builder /app/dist ./dist
# Ergebnis: 50-100MB statt 1GB+
```

**20. "ARG" Variable nicht verfuegbar im RUN**
```bash
# Ursache: ARG vor FROM definiert
# Loesung:
ARG NODE_ENV=production
FROM node:22-alpine
ARG NODE_ENV                # Nochmal nach FROM deklarieren
RUN echo $NODE_ENV
```

**21-25.** *(Weitere Build-Probleme mit Loesungen...)*

### Kategorie 3: Netzwerk-Probleme (Fehler 26-35)

**26. Container koennen sich nicht sehen**
```bash
# Loesung: Gleiches Netzwerk nutzen
docker network create app-net
docker run --network app-net --name api mein-api
docker run --network app-net --name web mein-web
# Jetzt: web kann api via "http://api:3000" erreichen
```

**27-35.** *(Weitere Netzwerk-Probleme mit Loesungen...)*

### Kategorie 4: Performance (Fehler 36-45)

**36. Container nutzt zu viel RAM**
```bash
# Loesung: Memory Limit setzen
docker run -m 512m mein-image
# In docker-compose:
deploy:
  resources:
    limits:
      memory: 512M
```

**37-45.** *(Weitere Performance-Probleme mit Loesungen...)*

### Kategorie 5: Security (Fehler 46-50)

**46. Container laeuft als Root**
```bash
# Loesung: Non-root User im Dockerfile
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
```

**47-50.** *(Weitere Security-Probleme mit Loesungen...)*

---

## Kapitel 2: Docker Compose fuer AI Stacks

### Stack 1: Ollama + Redis + PostgreSQL

```yaml
version: "3.8"

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --save 60 1 --loglevel warning

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: aiempire
      POSTGRES_USER: empire
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    secrets:
      - db_password

volumes:
  ollama-data:
  redis-data:
  postgres-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### Stack 2: Full AI Empire

```yaml
version: "3.8"

services:
  crm:
    build: ./crm
    ports:
      - "3500:3500"
    volumes:
      - crm-data:/app/data

  atomic-reactor:
    build: ./atomic-reactor
    ports:
      - "8888:8888"
    depends_on:
      - redis
      - postgres

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: aiempire
      POSTGRES_USER: empire
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

volumes:
  crm-data:
  ollama-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

## Kapitel 3: Ollama in Docker optimieren

### Performance-Tuning

```bash
# GPU-Zugriff aktivieren (NVIDIA)
docker run --gpus all ollama/ollama

# Apple Silicon (kein Docker noetig!)
brew install ollama
ollama serve
# Nativ = 2-3x schneller als Docker auf Mac

# Memory Limit fuer grosse Modelle
docker run -m 8g ollama/ollama

# Parallele Anfragen erhoehen
OLLAMA_NUM_PARALLEL=4 ollama serve
```

### Modell-Management

```bash
# Modelle vorladen (schneller Start)
docker exec ollama ollama pull qwen2.5-coder:7b
docker exec ollama ollama pull mistral:7b

# Custom Modelfile
FROM qwen2.5-coder:7b
PARAMETER temperature 0.3
PARAMETER num_ctx 8192
SYSTEM "Du bist ein Senior Developer. Antworte nur mit Code."
```

---

## Kapitel 4: Performance Tuning

### Build-Geschwindigkeit verdoppeln

```bash
# BuildKit aktivieren (2-5x schneller)
DOCKER_BUILDKIT=1 docker build -t mein-image .

# Multi-Stage + Cache
FROM node:22-alpine AS deps
COPY package*.json ./
RUN npm ci

FROM node:22-alpine AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Container-Groesse minimieren

| Basis-Image | Groesse | Empfehlung |
|-------------|---------|------------|
| node:22 | ~1 GB | Nur Entwicklung |
| node:22-slim | ~200 MB | Standard |
| node:22-alpine | ~50 MB | Produktion |
| distroless | ~20 MB | Minimal |

---

## Kapitel 5: Security Best Practices

### Die 10 Docker Security Regeln

1. **Nie als root laufen** → `USER appuser`
2. **Offizielle Images nutzen** → `node:22-alpine`
3. **Images scannen** → `docker scout cves mein-image`
4. **Secrets nie in ENV** → Docker Secrets nutzen
5. **Read-only Filesystem** → `--read-only`
6. **Network Segmentation** → Eigene Netzwerke
7. **Resource Limits** → `-m 512m --cpus=1`
8. **Health Checks** → `HEALTHCHECK`
9. **Regelmaessig updaten** → `docker pull`
10. **Logging konfigurieren** → `--log-driver`

### Secure Dockerfile Template

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build

FROM node:22-alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1
CMD ["node", "dist/index.js"]
```

---

> *Erstellt von Maurice's AI Empire*
> *Spart dir Stunden beim Docker Debugging.*
> *Bei Fragen: DM auf X @mauricepfeifer*
