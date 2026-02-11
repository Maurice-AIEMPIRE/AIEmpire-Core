#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# AIEmpire-Core — GCE VM Bootstrap Script
# ═══════════════════════════════════════════════════════════════
# For deploying on a single GCE VM instead of Cloud Run.
# Useful for Ollama (needs GPU/CPU), n8n, and full-stack dev.
#
# Usage:
#   # Create VM and run bootstrap
#   gcloud compute instances create empire-vm \
#     --zone=europe-west1-b \
#     --machine-type=e2-standard-4 \
#     --image-family=ubuntu-2204-lts \
#     --image-project=ubuntu-os-cloud \
#     --boot-disk-size=50GB \
#     --tags=http-server,https-server \
#     --metadata-from-file=startup-script=cloud-deploy/scripts/bootstrap_vm.sh
#
#   # Or SSH in and run manually:
#   gcloud compute ssh empire-vm -- 'bash -s' < cloud-deploy/scripts/bootstrap_vm.sh
# ═══════════════════════════════════════════════════════════════

export DEBIAN_FRONTEND=noninteractive

echo "═══════════════════════════════════════════════════════"
echo "  AIEmpire-Core VM Bootstrap"
echo "═══════════════════════════════════════════════════════"

# ─── System Updates ─────────────────────────────────────────
echo "[1/8] System updates..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    git curl wget unzip jq htop \
    python3 python3-pip python3-venv \
    docker.io docker-compose-v2 \
    nginx certbot python3-certbot-nginx \
    redis-server postgresql postgresql-client

# ─── Docker Setup ───────────────────────────────────────────
echo "[2/8] Docker setup..."
systemctl enable docker
systemctl start docker
usermod -aG docker "$USER" 2>/dev/null || true

# ─── Ollama (Local AI Models) ──────────────────────────────
echo "[3/8] Installing Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

# Pull optimized models for 16GB RAM
systemctl enable ollama
systemctl start ollama
sleep 5

ollama pull phi:q4 &        # 600MB - fast reasoning
ollama pull qwen2.5-coder:7b &  # Code generation
wait
echo "Ollama models ready"

# ─── Clone Repository ──────────────────────────────────────
echo "[4/8] Cloning AIEmpire-Core..."
EMPIRE_DIR="/opt/aiempire"
mkdir -p "$EMPIRE_DIR"

if [ ! -d "$EMPIRE_DIR/.git" ]; then
    git clone https://github.com/mauricepfeifer-ctrl/AIEmpire-Core.git "$EMPIRE_DIR"
else
    cd "$EMPIRE_DIR" && git pull origin main
fi

cd "$EMPIRE_DIR"

# ─── Python Environment ────────────────────────────────────
echo "[5/8] Python environment..."
python3 -m venv /opt/empire-venv
source /opt/empire-venv/bin/activate

pip install -q -r requirements.txt 2>/dev/null || \
pip install -q \
    fastapi uvicorn[standard] aiohttp httpx \
    asyncpg redis aiofiles pyyaml \
    pydantic python-dotenv python-multipart

# ─── PostgreSQL Setup ──────────────────────────────────────
echo "[6/8] PostgreSQL setup..."
sudo -u postgres psql -c "CREATE USER empire_admin WITH PASSWORD 'empire_$(openssl rand -hex 8)';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE empire OWNER empire_admin;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE empire TO empire_admin;" 2>/dev/null || true

# ─── Redis Setup ────────────────────────────────────────────
echo "[7/8] Redis setup..."
systemctl enable redis-server
systemctl start redis-server

# ─── Systemd Services ──────────────────────────────────────
echo "[8/8] Creating systemd services..."

# Empire API Service
cat > /etc/systemd/system/empire-api.service << 'SVC'
[Unit]
Description=AIEmpire API Server
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aiempire
Environment=PATH=/opt/empire-venv/bin:/usr/local/bin:/usr/bin
ExecStart=/opt/empire-venv/bin/python -m uvicorn empire_api.main:app --host 0.0.0.0 --port 3333
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC

# Atomic Reactor Service
cat > /etc/systemd/system/atomic-reactor.service << 'SVC'
[Unit]
Description=Atomic Reactor Task Runner
After=network.target empire-api.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aiempire
Environment=PATH=/opt/empire-venv/bin:/usr/local/bin:/usr/bin
ExecStart=/opt/empire-venv/bin/python -m uvicorn atomic_reactor.main:app --host 0.0.0.0 --port 8888
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC

# Workflow Daemon (5-step loop every 6h)
cat > /etc/systemd/system/empire-workflow.service << 'SVC'
[Unit]
Description=AIEmpire Workflow Daemon
After=network.target empire-api.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aiempire
Environment=PATH=/opt/empire-venv/bin:/usr/local/bin:/usr/bin
ExecStart=/opt/empire-venv/bin/python workflow_system/orchestrator.py
Restart=always
RestartSec=21600

[Install]
WantedBy=multi-user.target
SVC

# Cowork Daemon (every 30 min)
cat > /etc/systemd/system/empire-cowork.service << 'SVC'
[Unit]
Description=AIEmpire Cowork Daemon
After=network.target empire-api.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aiempire
Environment=PATH=/opt/empire-venv/bin:/usr/local/bin:/usr/bin
ExecStart=/opt/empire-venv/bin/python workflow_system/cowork.py --daemon --interval 1800
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVC

# Gemini Mirror Daemon
cat > /etc/systemd/system/gemini-mirror.service << 'SVC'
[Unit]
Description=Gemini Mirror Daemon
After=network.target empire-api.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aiempire
Environment=PATH=/opt/empire-venv/bin:/usr/local/bin:/usr/bin
ExecStart=/opt/empire-venv/bin/python gemini-mirror/gemini_empire.py daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVC

# Enable and start services
systemctl daemon-reload
systemctl enable empire-api atomic-reactor empire-cowork gemini-mirror
systemctl start empire-api
systemctl start atomic-reactor
sleep 2
systemctl start empire-cowork
systemctl start gemini-mirror

# ─── Nginx Reverse Proxy ───────────────────────────────────
cat > /etc/nginx/sites-available/empire << 'NGINX'
server {
    listen 80;
    server_name _;

    # Empire API
    location /api/ {
        proxy_pass http://127.0.0.1:3333/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Atomic Reactor
    location /reactor/ {
        proxy_pass http://127.0.0.1:8888/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # CRM
    location /crm/ {
        proxy_pass http://127.0.0.1:3500/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        return 200 '{"status":"ok","services":["api","reactor","crm","ollama"]}';
        add_header Content-Type application/json;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/empire /etc/nginx/sites-enabled/empire
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ─── Firewall ──────────────────────────────────────────────
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw allow 22/tcp   # SSH
ufw --force enable

# ─── Final Status ──────────────────────────────────────────
echo
echo "═══════════════════════════════════════════════════════"
echo "  VM BOOTSTRAP COMPLETE"
echo "═══════════════════════════════════════════════════════"
echo
echo "Services:"
systemctl is-active empire-api && echo "  Empire API:      RUNNING (port 3333)" || echo "  Empire API:      STOPPED"
systemctl is-active atomic-reactor && echo "  Atomic Reactor:  RUNNING (port 8888)" || echo "  Atomic Reactor:  STOPPED"
systemctl is-active empire-cowork && echo "  Cowork Daemon:   RUNNING" || echo "  Cowork Daemon:   STOPPED"
systemctl is-active gemini-mirror && echo "  Gemini Mirror:   RUNNING" || echo "  Gemini Mirror:   STOPPED"
systemctl is-active ollama && echo "  Ollama:          RUNNING (port 11434)" || echo "  Ollama:          STOPPED"
systemctl is-active redis-server && echo "  Redis:           RUNNING (port 6379)" || echo "  Redis:           STOPPED"
systemctl is-active postgresql && echo "  PostgreSQL:      RUNNING (port 5432)" || echo "  PostgreSQL:      STOPPED"
systemctl is-active nginx && echo "  Nginx:           RUNNING (port 80)" || echo "  Nginx:           STOPPED"
echo
echo "Access: http://$(curl -s ifconfig.me)/health"
echo "SSL:    certbot --nginx -d yourdomain.com"
echo
