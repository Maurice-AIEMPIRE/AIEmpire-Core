# AI Empire — Google Cloud Deployment Guide

Account: mauricepfeiferai@gmail.com
Projekt: ai-empire-486415
Region: europe-west4 (Niederlande, nah an Deutschland)

## Voraussetzungen installieren (auf deinem Mac)

```bash
# Google Cloud SDK
brew install google-cloud-sdk

# Terraform (Infrastruktur)
brew install terraform

# Podman (Container, Open Source Docker-Ersatz)
brew install podman
podman machine init
podman machine start
```

## Schritt 1: Google Cloud einrichten

```bash
# Login
gcloud auth login

# Projekt setzen
gcloud config set project ai-empire-486415
gcloud config set compute/region europe-west4

# APIs aktivieren
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable compute.googleapis.com
```

## Schritt 2: Deployment (1 Befehl)

```bash
cd ~/AIEmpire-Core
./cloud/deploy.sh
```

Das macht automatisch:
1. Container bauen (Dockerfile)
2. Push zu Artifact Registry
3. Deploy auf Cloud Run
4. Data sync zu Cloud Storage

## Schritt 3: Testen

```bash
# Cloud API testen
URL=$(gcloud run services describe empire-api --region=europe-west4 --format="value(status.url)")
curl "$URL/health"
curl "$URL/status"
curl -X POST "$URL/ask?prompt=Hallo+Empire"
```

## Schritt 4: Sync einrichten (Mac <-> Cloud)

```bash
# Einmalig: Mac -> Cloud
./cloud/sync_local_cloud.sh up

# Cloud -> Mac
./cloud/sync_local_cloud.sh down

# Auto-Sync alle 5 Minuten
./cloud/sync_local_cloud.sh watch
```

## Open Source Stack

| Tool | Funktion | Lizenz |
|------|----------|--------|
| Ollama | Lokale AI Models | MIT |
| FastAPI | REST API | MIT |
| Redis | Cache/Queue | BSD |
| PostgreSQL | Datenbank | PostgreSQL |
| n8n | Automation | Sustainable Use |
| Terraform | Infrastructure | MPL 2.0 |
| Podman | Container | Apache 2.0 |
| Python | Runtime | PSF |

## Kosten (geschaetzt)

| Service | Kosten/Monat |
|---------|-------------|
| Cloud Run (0-3 Instanzen) | 0-50 EUR |
| Cloud Storage (10 GB) | ca. 1 EUR |
| Artifact Registry | ca. 1 EUR |
| GPU VM (optional, preemptible) | 50-200 EUR |
| **Gesamt (ohne GPU)** | **ca. 5-50 EUR** |

Cloud Run skaliert auf 0 wenn nicht genutzt = fast kostenlos.
GPU VM nur wenn du schwere AI-Aufgaben in der Cloud brauchst.

## Architektur

```
Mac Mini (lokal)                 Google Cloud
┌────────────────┐               ┌──────────────────┐
│  Ollama (AI)   │  ←── sync ──→ │  Cloud Run (API) │
│  Redis         │               │  Cloud Storage   │
│  PostgreSQL    │               │  Artifact Reg.   │
│  n8n           │               │  [GPU VM]        │
│  empire_boot   │               │  cloud_api.py    │
└────────────────┘               └──────────────────┘
        ↕                                ↕
   100% lokal                    Cloud-Power bei Bedarf
   0 EUR Kosten                  Skalierbar
```
