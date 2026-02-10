#!/bin/bash
# n8n Setup Script - Automated Setup

set -e

echo "🚀 Starting n8n Setup..."

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker not running. Starting Docker..."
    open -a Docker || echo "⚠️ Please start Docker manually"
    sleep 5
fi

# Stop existing n8n container if running
docker compose down -v 2>/dev/null || true

# Create docker-compose for n8n
cat > /tmp/n8n-docker-compose.yml << 'EOF'
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_SECURE_COOKIE=false
      - NODE_ENV=production
      - N8N_EDITOR_BASE_URL=http://localhost:5678/
      - WEBHOOK_TUNNEL_URL=http://localhost:5678/
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - n8n_network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: n8n-postgres
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=n8n_secure_password
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - n8n_network
    restart: unless-stopped

volumes:
  n8n_data:
  postgres_data:

networks:
  n8n_network:
    driver: bridge
EOF

# Start n8n with Docker Compose
echo "📦 Starting n8n with Docker Compose..."
docker compose -f /tmp/n8n-docker-compose.yml up -d

# Wait for n8n to be ready
echo "⏳ Waiting for n8n to start (30 seconds)..."
sleep 30

# Try to get n8n status
echo "✅ n8n should be running at http://localhost:5678"
echo "📝 First time setup:"
echo "   1. Go to http://localhost:5678"
echo "   2. Create your user account"
echo "   3. Save API Key to .env: N8N_API_KEY=xxx"
echo ""
echo "💾 To get API Key after login:"
echo "   curl -X GET http://localhost:5678/api/v1/me -H 'X-N8N-API-KEY: YOUR_KEY'"

# Add n8n to .env if not present
if ! grep -q "N8N_API_KEY" /Users/maurice/AIEmpire-Core/.env 2>/dev/null; then
    echo "N8N_API_KEY=add_after_setup" >> /Users/maurice/AIEmpire-Core/.env
fi

echo "✅ n8n setup complete!"
