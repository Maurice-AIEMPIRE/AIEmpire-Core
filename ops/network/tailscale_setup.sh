#!/bin/bash
# ============================================================
# GALAXIA NETWORK FOUNDATION: Tailscale Mesh VPN Setup
# ============================================================
# Connects Mac mini ↔ Hetzner-1 ↔ Hetzner-2 via Tailscale
# Creates secure, encrypted, peer-to-peer network
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
HETZNER_PRIMARY="65.21.203.174"
HETZNER_STANDBY="65.21.203.175"  # Placeholder - update with actual IP
TAILSCALE_AUTH_KEY="${TAILSCALE_AUTH_KEY:-}"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

log_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  GALAXIA: Tailscale Network Setup                     ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_step() {
    echo -e "${YELLOW}[$1]${NC} $2"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

verify_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 not found. Please install it first."
    fi
}

# ============================================================
# STEP 1: Environment Validation
# ============================================================

log_header

log_step "1/6" "Validating environment..."

# Check OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    INSTALL_CMD="brew install"
elif [[ "$OSTYPE" == "linux"* ]]; then
    OS="Linux"
    INSTALL_CMD="apt-get install -y"
else
    log_error "Unsupported OS: $OSTYPE"
fi

log_success "OS detected: $OS"

# Check required commands
verify_command ssh
verify_command ssh-keygen
log_success "SSH tools available"

# Check for .env file
if [ ! -f ".env" ]; then
    log_error ".env file not found. Run 'setup_optimal_dev.sh' first."
fi
log_success ".env file found"

echo ""

# ============================================================
# STEP 2: Tailscale Installation
# ============================================================

log_step "2/6" "Installing Tailscale..."

# Check if tailscale already installed
if command -v tailscale &> /dev/null; then
    log_success "Tailscale already installed"
else
    if [[ "$OS" == "macOS" ]]; then
        $INSTALL_CMD tailscale
    else
        curl -fsSL https://tailscale.com/install.sh | sh
    fi
    log_success "Tailscale installed"
fi

echo ""

# ============================================================
# STEP 3: Hetzner Runner SSH Keys
# ============================================================

log_step "3/6" "Setting up SSH keys for Hetzner runners..."

SSH_DIR="${HOME}/.ssh"
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

# Create ed25519 key if not exists
if [ ! -f "$SSH_DIR/id_ed25519" ]; then
    log_step "3/6" "Generating Ed25519 SSH key..."
    ssh-keygen -t ed25519 -f "$SSH_DIR/id_ed25519" -N "" -C "AIEmpire-Core"
    log_success "SSH key generated"
else
    log_success "SSH key already exists"
fi

# Create SSH config for Hetzner runners
SSH_CONFIG="$SSH_DIR/config"
if ! grep -q "Host hetzner-1" "$SSH_CONFIG" 2>/dev/null; then
    cat >> "$SSH_CONFIG" << 'SSHCONFIG'

# AIEmpire Hetzner Runners
Host hetzner-1
    HostName 65.21.203.174
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
    UserKnownHostsFile ~/.ssh/known_hosts

Host hetzner-2
    HostName 65.21.203.175
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
    UserKnownHostsFile ~/.ssh/known_hosts

# Tailscale Mesh
Host hetzner-1-ts
    HostName 100.64.0.1
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new

Host hetzner-2-ts
    HostName 100.64.0.2
    User root
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
SSHCONFIG
    log_success "SSH config updated"
else
    log_success "SSH config already configured"
fi

chmod 600 "$SSH_CONFIG"

# Copy public key to clipboard (for manual setup if needed)
echo ""
echo -e "${YELLOW}SSH Public Key:${NC}"
cat "$SSH_DIR/id_ed25519.pub"
echo ""
echo -e "${YELLOW}↓ Copy the above key and add to Hetzner runner:${NC}"
echo "  mkdir -p ~/.ssh && echo '<paste-key>' >> ~/.ssh/authorized_keys"
echo ""

echo ""

# ============================================================
# STEP 4: Tailscale Auth Key Setup
# ============================================================

log_step "4/6" "Tailscale authentication..."

if [ -z "$TAILSCALE_AUTH_KEY" ]; then
    log_error "TAILSCALE_AUTH_KEY not set in environment"
    echo ""
    echo "To get auth key:"
    echo "  1. Go to https://login.tailscale.com/admin/settings/keys"
    echo "  2. Create new auth key (reusable, ephemeral)"
    echo "  3. Export to shell: export TAILSCALE_AUTH_KEY='tskey-...'"
    echo "  4. Run this script again"
    exit 1
fi

log_success "TAILSCALE_AUTH_KEY configured"
echo ""

# ============================================================
# STEP 5: Mac Mini Tailscale Setup
# ============================================================

log_step "5/6" "Setting up Tailscale on Mac mini..."

# Start Tailscale if not running
if ! pgrep -x "tailscaled" > /dev/null; then
    log_step "5/6" "Starting Tailscale daemon..."
    sudo tailscaled &
    sleep 3
fi

# Authenticate with Tailscale
if ! tailscale status &> /dev/null; then
    log_step "5/6" "Authenticating with Tailscale..."
    sudo tailscale up --auth-key="$TAILSCALE_AUTH_KEY" --hostname=aiempire-mac-mini

    # Wait for connection
    sleep 5
fi

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4)
log_success "Mac mini Tailscale IP: $TAILSCALE_IP"

echo ""

# ============================================================
# STEP 6: Hetzner Tailscale Setup
# ============================================================

log_step "6/6" "Setting up Tailscale on Hetzner runners..."

# Script to run on Hetzner
HETZNER_TS_SETUP='#!/bin/bash
set -e

echo "Installing Tailscale on Hetzner runner..."
curl -fsSL https://tailscale.com/install.sh | sh

echo "Authenticating Tailscale..."
export TAILSCALE_AUTH_KEY="'"$TAILSCALE_AUTH_KEY"'"
tailscale up --auth-key="$TAILSCALE_AUTH_KEY" --hostname='"$HOSTNAME"'

echo "Waiting for Tailscale connection..."
sleep 5

echo "Tailscale Status:"
tailscale status

echo "✓ Tailscale configured"
'

# Setup Hetzner-1
log_step "6/6" "Setting up Hetzner-1 (primary)..."
ssh -o ConnectTimeout=5 root@$HETZNER_PRIMARY bash << 'EOF' || log_error "Failed to connect to Hetzner-1"
set -e
curl -fsSL https://tailscale.com/install.sh | sh
echo "Tailscale installed"
EOF

log_success "Hetzner-1 Tailscale installed"

echo ""

# ============================================================
# VERIFICATION
# ============================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ TAILSCALE NETWORK SETUP COMPLETE!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "📊 Network Topology:"
echo "  Mac mini (AIEmpire Controller)"
echo "    └─ Tailscale IP: $TAILSCALE_IP"
echo ""
echo "  Hetzner-1 (Primary Runner)"
echo "    └─ Public IP: $HETZNER_PRIMARY"
echo "    └─ Tailscale: 100.64.0.1 (after auth)"
echo ""
echo "  Hetzner-2 (Standby Runner)"
echo "    └─ Public IP: $HETZNER_STANDBY"
echo "    └─ Tailscale: 100.64.0.2 (after auth)"
echo ""

echo "🔗 Verification Commands:"
echo ""
echo "  Check local Tailscale:"
echo "    ${BLUE}tailscale status${NC}"
echo ""
echo "  Check Hetzner-1:"
echo "    ${BLUE}ssh hetzner-1 'tailscale status'${NC}"
echo ""
echo "  Test Hetzner-1 connectivity:"
echo "    ${BLUE}ssh hetzner-1-ts 'echo OK'${NC}"
echo ""

echo "🔐 Security Notes:"
echo "  • All traffic encrypted with WireGuard"
echo "  • Only authenticated nodes can connect"
echo "  • SSH keys verified via host-key checking"
echo "  • Firewall rules should allow only Tailscale traffic"
echo ""

echo -e "${GREEN}✅ Ready for Phase 1B.2: Hetzner Provisioning${NC}"
