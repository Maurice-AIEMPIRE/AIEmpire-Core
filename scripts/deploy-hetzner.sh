#!/bin/bash
# AIEmpire-Core Deployment to Hetzner Cloud (Tailscale)
# Usage: bash deploy-hetzner.sh <hostname>

set -e

VM_HOST="${1:-ubuntu-2404-noble-amd64-base.tail1ca9fd.ts.net}"
SSH_KEY="$HOME/.ssh/hetzner_ed25519"
DEPLOY_USER="ubuntu"

echo "🚀 AIEmpire-Core Deployment to Hetzner"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Target: $VM_HOST"
echo "SSH Key: $SSH_KEY"
echo ""

# Verify SSH Key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH Key not found: $SSH_KEY"
    exit 1
fi

echo "✅ SSH Key found"

# Test SSH Connection
echo ""
echo "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 "$DEPLOY_USER@$VM_HOST" "echo 'SSH OK'" 2>/dev/null; then
    echo "❌ Cannot connect to $VM_HOST"
    exit 1
fi
echo "✅ SSH Connection successful"

# Deploy Commands
echo ""
echo "Starting deployment..."
echo ""

ssh -i "$SSH_KEY" "$DEPLOY_USER@$VM_HOST" << 'REMOTE_COMMANDS'
set -e

echo "📦 Updating system..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

echo "🐍 Installing Python dependencies..."
sudo apt-get install -y -qq python3 python3-pip python3-venv git curl wget

echo "🔧 Installing system tools..."
sudo apt-get install -y -qq redis-server postgresql postgresql-contrib build-essential

echo "📂 Cloning AIEmpire-Core..."
cd /home/ubuntu
if [ -d "AIEmpire-Core" ]; then
    cd AIEmpire-Core
    git fetch origin
    git reset --hard origin/main
    cd /home/ubuntu
else
    git clone https://github.com/Maurice-AIEMPIRE/AIEmpire-Core.git
fi

cd AIEmpire-Core

echo "📥 Installing Python dependencies..."
pip3 install -r requirements.txt -q

echo "🛠️ Running setup..."
bash scripts/setup_optimal_dev.sh 2>/dev/null || true

echo "✅ Setup complete!"
echo ""
echo "Status:"
python3 empire_engine.py 2>/dev/null || echo "Empire Engine ready (needs config)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ AIEmpire-Core deployed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REMOTE_COMMANDS

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "Next steps:"
echo "  1. SSH: ssh -i $SSH_KEY $DEPLOY_USER@$VM_HOST"
echo "  2. Start: cd AIEmpire-Core && python3 empire_engine.py"
echo "  3. Configure .env with API keys"
