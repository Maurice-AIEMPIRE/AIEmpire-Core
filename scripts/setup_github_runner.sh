#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# GITHUB ACTIONS SELF-HOSTED RUNNER — AIEmpire-Core
# ══════════════════════════════════════════════════════════════════════════════
#
# Sets up a self-hosted GitHub Actions runner on the Hetzner server.
# The runner auto-starts on boot via systemd and auto-updates.
#
# Prerequisites:
#   - GitHub repo: Maurice-AIEMPIRE/AIEmpire-Core
#   - GITHUB_TOKEN with repo + admin:org scope
#   - Ubuntu 24.04 (Hetzner server)
#
# Usage:
#   bash scripts/setup_github_runner.sh
#   bash scripts/setup_github_runner.sh --token ghp_xxx
#
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Config ─────────────────────────────────────────────────────────────────
RUNNER_VERSION="2.322.0"
RUNNER_DIR="/opt/actions-runner"
RUNNER_USER="runner"
REPO_OWNER="Maurice-AIEMPIRE"
REPO_NAME="AIEmpire-Core"
LABELS="self-hosted,linux,x64,hetzner,production"

# ─── Colors ─────────────────────────────────────────────────────────────────
R='\033[0;31m'
G='\033[0;32m'
Y='\033[1;33m'
B='\033[0;34m'
W='\033[1;37m'
N='\033[0m'

log() { echo -e "  ${G}[OK]${N}      $*"; }
warn() { echo -e "  ${Y}[WARN]${N}    $*"; }
fail() { echo -e "  ${R}[FAIL]${N}    $*"; exit 1; }
info() { echo -e "  ${B}[INFO]${N}    $*"; }

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║     GITHUB ACTIONS RUNNER SETUP — AIEmpire-Core          ║${N}"
echo -e "${W}║     Self-Hosted • Auto-Update • systemd                  ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""

# ─── Get Token ──────────────────────────────────────────────────────────────
TOKEN=""
if [ "${1:-}" = "--token" ] && [ -n "${2:-}" ]; then
    TOKEN="$2"
elif [ -n "${GITHUB_TOKEN:-}" ]; then
    TOKEN="$GITHUB_TOKEN"
elif [ -f /opt/aiempire/.env ]; then
    TOKEN=$(grep -oP '^GITHUB_TOKEN=\K.*' /opt/aiempire/.env 2>/dev/null || true)
fi

if [ -z "$TOKEN" ]; then
    fail "No GitHub token found. Use: --token ghp_xxx or set GITHUB_TOKEN in .env"
fi

# ─── Get Registration Token ────────────────────────────────────────────────
info "Getting runner registration token..."
REG_TOKEN=$(curl -s -X POST \
    -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/runners/registration-token" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

if [ -z "$REG_TOKEN" ]; then
    fail "Could not get registration token. Check GITHUB_TOKEN permissions (needs repo + admin scope)."
fi
log "Registration token obtained"

# ─── Create Runner User ────────────────────────────────────────────────────
if ! id "$RUNNER_USER" &>/dev/null; then
    info "Creating runner user..."
    useradd -m -s /bin/bash "$RUNNER_USER"
    usermod -aG docker "$RUNNER_USER" 2>/dev/null || true
    log "User '$RUNNER_USER' created"
else
    log "User '$RUNNER_USER' exists"
fi

# ─── Download Runner ───────────────────────────────────────────────────────
if [ -f "$RUNNER_DIR/.runner" ]; then
    warn "Runner already configured at $RUNNER_DIR"
    echo -e "  ${Y}[WARN]${N}    To reconfigure, remove $RUNNER_DIR first"
    echo -e "  ${Y}[WARN]${N}    Or run: $RUNNER_DIR/config.sh remove --token \$TOKEN"
    echo ""
else
    info "Downloading GitHub Actions Runner v${RUNNER_VERSION}..."
    mkdir -p "$RUNNER_DIR"

    RUNNER_ARCH="linux-x64"
    RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"

    curl -sL "$RUNNER_URL" | tar xz -C "$RUNNER_DIR"
    chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"
    log "Runner downloaded to $RUNNER_DIR"

    # ─── Configure Runner ──────────────────────────────────────────────────
    info "Configuring runner..."
    cd "$RUNNER_DIR"
    sudo -u "$RUNNER_USER" ./config.sh \
        --url "https://github.com/$REPO_OWNER/$REPO_NAME" \
        --token "$REG_TOKEN" \
        --name "hetzner-production" \
        --labels "$LABELS" \
        --work "_work" \
        --unattended \
        --replace

    log "Runner configured for $REPO_OWNER/$REPO_NAME"
fi

# ─── systemd Service ───────────────────────────────────────────────────────
info "Installing systemd service..."
cat > /etc/systemd/system/github-runner.service << 'SERVICEEOF'
[Unit]
Description=GitHub Actions Runner (AIEmpire-Core)
After=network.target docker.service

[Service]
Type=simple
User=runner
Group=runner
WorkingDirectory=/opt/actions-runner
ExecStart=/opt/actions-runner/run.sh
Restart=always
RestartSec=10
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=5min

# Environment
Environment="DOTNET_CLI_TELEMETRY_OPTOUT=1"
Environment="RUNNER_ALLOW_RUNASROOT=0"

# Hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/actions-runner /opt/aiempire /var/log/aiempire /tmp
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable github-runner.service
systemctl start github-runner.service
log "github-runner.service enabled and started"

# ─── Verify ────────────────────────────────────────────────────────────────
sleep 3
if systemctl is-active --quiet github-runner.service; then
    log "Runner is ACTIVE and listening for jobs"
else
    warn "Runner service started but may not be active yet. Check: systemctl status github-runner"
fi

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║                RUNNER SETUP COMPLETE                      ║${N}"
echo -e "${W}╠═══════════════════════════════════════════════════════════╣${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  Runner:   hetzner-production                             ║${N}"
echo -e "${W}║  Labels:   $LABELS  ║${N}"
echo -e "${W}║  Service:  github-runner.service                          ║${N}"
echo -e "${W}║  Status:   systemctl status github-runner                 ║${N}"
echo -e "${W}║  Logs:     journalctl -u github-runner -f                 ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""
