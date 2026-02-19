#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# GITHUB SELF-HOSTED RUNNER SETUP — AIEmpire-Core
# ══════════════════════════════════════════════════════════════════════════════
#
# Installiert einen GitHub Actions Self-Hosted Runner auf deinem Server.
# Damit sind ALLE GitHub Actions Minutes KOSTENLOS und UNLIMITED.
#
# Voraussetzung: Du brauchst ein GitHub Personal Access Token (PAT)
#   mit "repo" und "admin:org" Permissions.
#
# Usage:
#   chmod +x scripts/setup_github_runner.sh
#   ./scripts/setup_github_runner.sh
#
# ══════════════════════════════════════════════════════════════════════════════

set -e

G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
W='\033[1;37m'
N='\033[0m'

RUNNER_VERSION="2.321.0"
RUNNER_DIR="/opt/actions-runner"
RUNNER_USER="runner"
REPO_URL="https://github.com/Maurice-AIEMPIRE/AIEmpire-Core"

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║   GITHUB SELF-HOSTED RUNNER — UNLIMITED FREE ACTIONS     ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""

# ─── Check root ─────────────────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${R}[ERROR]${N} Dieses Script muss als root laufen (sudo)"
    exit 1
fi

# ─── Get GitHub Token ────────────────────────────────────────────────────────
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${Y}GitHub Personal Access Token benoetigt.${N}"
    echo -e "Erstelle eins unter: https://github.com/settings/tokens"
    echo -e "Benoetigt: 'repo' Permissions"
    echo ""
    read -rp "GitHub Token: " GITHUB_TOKEN
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${R}[ERROR]${N} Kein Token angegeben. Abbruch."
    exit 1
fi

# ─── Get Runner Registration Token ──────────────────────────────────────────
echo -e "${B}[INFO]${N} Hole Runner Registration Token..."

REG_TOKEN=$(curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/Maurice-AIEMPIRE/AIEmpire-Core/actions/runners/registration-token" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

if [ -z "$REG_TOKEN" ]; then
    echo -e "${R}[ERROR]${N} Konnte Registration Token nicht holen."
    echo "Pruefe: Token-Permissions, Repository-Zugriff"
    exit 1
fi
echo -e "${G}[OK]${N} Registration Token erhalten"

# ─── Create runner user ─────────────────────────────────────────────────────
if ! id "$RUNNER_USER" &>/dev/null; then
    echo -e "${B}[INFO]${N} Erstelle User: $RUNNER_USER"
    useradd -m -s /bin/bash "$RUNNER_USER"
    usermod -aG docker "$RUNNER_USER" 2>/dev/null || true
fi

# ─── Install runner ─────────────────────────────────────────────────────────
echo -e "${B}[INFO]${N} Installiere GitHub Actions Runner v${RUNNER_VERSION}..."

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

ARCH=$(uname -m)
case "$ARCH" in
    x86_64)  RUNNER_ARCH="x64" ;;
    aarch64) RUNNER_ARCH="arm64" ;;
    *)       echo -e "${R}[ERROR]${N} Architektur $ARCH nicht unterstuetzt"; exit 1 ;;
esac

RUNNER_TAR="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_TAR}"

if [ ! -f "$RUNNER_TAR" ]; then
    curl -o "$RUNNER_TAR" -L "$RUNNER_URL"
fi
tar xzf "$RUNNER_TAR"

chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"

# ─── Configure runner ───────────────────────────────────────────────────────
echo -e "${B}[INFO]${N} Konfiguriere Runner..."

su - "$RUNNER_USER" -c "
    cd $RUNNER_DIR && \
    ./config.sh \
        --url $REPO_URL \
        --token $REG_TOKEN \
        --name 'hetzner-empire-runner' \
        --labels 'self-hosted,linux,hetzner,x64' \
        --work '_work' \
        --unattended \
        --replace
"

echo -e "${G}[OK]${N} Runner konfiguriert"

# ─── Install as systemd service ─────────────────────────────────────────────
echo -e "${B}[INFO]${N} Installiere als systemd Service..."

cat > /etc/systemd/system/github-runner.service << 'UNIT'
[Unit]
Description=GitHub Actions Self-Hosted Runner
After=network.target

[Service]
Type=simple
User=runner
WorkingDirectory=/opt/actions-runner
ExecStart=/opt/actions-runner/run.sh
Restart=always
RestartSec=10
KillSignal=SIGTERM
TimeoutStopSec=5min

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable github-runner.service
systemctl start github-runner.service

# ─── Verify ─────────────────────────────────────────────────────────────────
sleep 3
if systemctl is-active --quiet github-runner.service; then
    echo -e "${G}[OK]${N} Runner laeuft als systemd Service"
else
    echo -e "${R}[WARN]${N} Runner Service gestartet aber Status unklar"
    echo "  Pruefe: systemctl status github-runner.service"
fi

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║              RUNNER SETUP COMPLETE                        ║${N}"
echo -e "${W}╠═══════════════════════════════════════════════════════════╣${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  Runner: hetzner-empire-runner                            ║${N}"
echo -e "${W}║  Labels: self-hosted, linux, hetzner, x64                 ║${N}"
echo -e "${W}║  Service: github-runner.service (autostart)               ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  Pruefe auf GitHub:                                       ║${N}"
echo -e "${W}║  Settings → Actions → Runners                            ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  GitHub Actions sind jetzt KOSTENLOS und UNLIMITED!       ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""
