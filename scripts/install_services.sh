#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# INSTALL SYSTEMD SERVICES — AIEmpire-Core
# ══════════════════════════════════════════════════════════════════════════════
# Copies .service and .timer files to systemd, enables them, and starts.
# Run as root on the Hetzner server.
#
# Usage: bash scripts/install_services.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICES_DIR="$PROJECT_DIR/systems"

G='\033[0;32m'
Y='\033[1;33m'
N='\033[0m'

echo ""
echo "Installing AIEmpire systemd services..."
echo ""

# Ensure log dir
mkdir -p /var/log/aiempire

# Copy all service/timer files
for F in "$SERVICES_DIR"/aiempire-*.service "$SERVICES_DIR"/aiempire-*.timer; do
    [ ! -f "$F" ] && continue
    NAME=$(basename "$F")
    cp "$F" "/etc/systemd/system/$NAME"
    echo -e "  ${G}[OK]${N} $NAME"
done

# Also install github-runner if it exists
if [ -f "$SERVICES_DIR/github-runner.service" ]; then
    cp "$SERVICES_DIR/github-runner.service" "/etc/systemd/system/"
    echo -e "  ${G}[OK]${N} github-runner.service"
fi

systemctl daemon-reload
echo ""

# Enable boot services
systemctl enable aiempire-bombproof.service 2>/dev/null && echo -e "  ${G}[ENABLED]${N} aiempire-bombproof (boot)" || true
systemctl enable aiempire-content.timer 2>/dev/null && echo -e "  ${G}[ENABLED]${N} aiempire-content.timer (every 4h)" || true

echo ""
echo -e "${Y}Start services manually:${N}"
echo "  systemctl start aiempire-crm"
echo "  systemctl start aiempire-empire-api"
echo "  systemctl start aiempire-content.timer"
echo ""
echo "Check status:"
echo "  systemctl status aiempire-crm"
echo "  journalctl -u aiempire-crm -f"
echo ""
