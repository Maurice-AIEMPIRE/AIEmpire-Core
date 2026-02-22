#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Configure OpenClaw for Tailscale Access (Mac + iPhone)
# Run once on the server: bash /opt/aiempire/deploy/configure_openclaw_access.sh
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

OPENCLAW_CONFIG="$HOME/.openclaw/config.yaml"
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
PORT=18789

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OpenClaw Tailscale Access Configurator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── Check prerequisites ────────────────────────────────────────
if ! command -v openclaw &>/dev/null; then
  echo "✗ openclaw not found in PATH"; exit 1
fi

if [ -z "$TAILSCALE_IP" ]; then
  echo "⚠  Tailscale not running — will bind on 0.0.0.0 (all interfaces)"
  BIND_ADDR="0.0.0.0"
else
  echo "✓ Tailscale IP: $TAILSCALE_IP"
  BIND_ADDR="0.0.0.0"
fi

# ─── Stop existing gateway ──────────────────────────────────────
echo ""
echo "1. Stopping OpenClaw gateway..."
if systemctl --user is-active --quiet openclaw-gateway.service 2>/dev/null; then
  systemctl --user stop openclaw-gateway.service
  echo "   ✓ Systemd service stopped"
elif pgrep -f "openclaw-gateway" &>/dev/null; then
  pkill -f "openclaw-gateway" || true
  sleep 2
  echo "   ✓ Gateway process stopped"
else
  echo "   ℹ Gateway not running (will start fresh)"
fi

# ─── Update config file ─────────────────────────────────────────
echo ""
echo "2. Patching config: bind 0.0.0.0 + use LiteLLM proxy..."

if [ -f "$OPENCLAW_CONFIG" ]; then
  cp "$OPENCLAW_CONFIG" "${OPENCLAW_CONFIG}.bak"
  echo "   ✓ Backup saved to ${OPENCLAW_CONFIG}.bak"

  # Change bind address from 127.0.0.1 to 0.0.0.0
  if grep -q "bind:" "$OPENCLAW_CONFIG"; then
    sed -i 's/bind: 127\.0\.0\.1/bind: 0.0.0.0/g' "$OPENCLAW_CONFIG"
    sed -i 's/bind: "127\.0\.0\.1"/bind: "0.0.0.0"/g' "$OPENCLAW_CONFIG"
  else
    # Add bind under gateway section
    sed -i '/gateway:/a\  bind: 0.0.0.0' "$OPENCLAW_CONFIG"
  fi

  # Point OpenClaw model to LiteLLM proxy (unified routing through Docker stack)
  # This lets OpenClaw use all models (qwen-7b, qwen-14b, deepseek-r1) via LiteLLM
  if grep -q "OPENAI_API_BASE\|openai_api_base\|api_base" "$OPENCLAW_CONFIG"; then
    sed -i 's|http://localhost:11434|http://localhost:4000|g' "$OPENCLAW_CONFIG"
    sed -i 's|http://127\.0\.0\.1:11434|http://localhost:4000|g' "$OPENCLAW_CONFIG"
  fi

  echo "   ✓ Config updated"
  echo ""
  echo "   Current gateway config:"
  grep -A5 "gateway:" "$OPENCLAW_CONFIG" 2>/dev/null || true
else
  echo "   ⚠  Config not found at $OPENCLAW_CONFIG"
  echo "   Trying openclaw config commands..."
fi

# ─── Apply via CLI if available ─────────────────────────────────
echo ""
echo "3. Applying settings via openclaw CLI..."
# Try CLI config commands (may not exist in all versions)
openclaw config set gateway.bind 0.0.0.0 2>/dev/null && echo "   ✓ CLI: bind set" || echo "   ℹ CLI config set not available, file edit applied"
openclaw config set gateway.port "$PORT" 2>/dev/null || true

# ─── Restart gateway ────────────────────────────────────────────
echo ""
echo "4. Starting gateway..."
if systemctl --user is-enabled --quiet openclaw-gateway.service 2>/dev/null; then
  systemctl --user start openclaw-gateway.service
  sleep 3
  if systemctl --user is-active --quiet openclaw-gateway.service; then
    echo "   ✓ Systemd service started"
  else
    echo "   ⚠  Service failed to start, check: systemctl --user status openclaw-gateway.service"
  fi
else
  # Start as background process with nohup
  nohup openclaw gateway --bind 0.0.0.0 --port "$PORT" > /tmp/openclaw-gateway.log 2>&1 &
  GATEWAY_PID=$!
  sleep 3
  if kill -0 "$GATEWAY_PID" 2>/dev/null; then
    echo "   ✓ Gateway started (pid $GATEWAY_PID)"
    echo "   ✓ Logs: tail -f /tmp/openclaw-gateway.log"
  else
    echo "   ⚠  Gateway failed. Check: cat /tmp/openclaw-gateway.log"
    cat /tmp/openclaw-gateway.log 2>/dev/null | tail -20
  fi
fi

# ─── Show dashboard token ───────────────────────────────────────
sleep 2
echo ""
echo "5. Getting dashboard URL..."
TOKEN_OUTPUT=$(openclaw dashboard --no-open 2>&1)
TOKEN=$(echo "$TOKEN_OUTPUT" | grep -oP '(?<=#token=)[a-f0-9]+' | head -1)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ACCESS URLS (all devices)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ -n "$TAILSCALE_IP" ] && [ -n "$TOKEN" ]; then
  echo "  🍎 Mac (Tailscale):"
  echo "     http://$TAILSCALE_IP:$PORT/#token=$TOKEN"
  echo ""
  echo "  📱 iPhone (Tailscale):"
  echo "     → Install 'Tailscale' app from App Store"
  echo "     → Connect to your Tailscale network"
  echo "     → Open Safari:"
  echo "     http://$TAILSCALE_IP:$PORT/#token=$TOKEN"
  echo ""
  echo "  💻 Mac SSH tunnel (alternative):"
  echo "     ssh -N -L $PORT:127.0.0.1:$PORT root@$TAILSCALE_IP"
  echo "     then: http://localhost:$PORT/#token=$TOKEN"
fi
echo ""
echo "  Token: $TOKEN"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "IMPORTANT: Save the token above — it does not change."
echo "Bookmark the URL on Mac and iPhone for instant access."
echo ""
