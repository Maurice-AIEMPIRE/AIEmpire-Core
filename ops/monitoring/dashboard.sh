#!/usr/bin/env bash
# AI Empire Simple Dashboard
# Version: 1.0
# Last Updated: 2026-02-10

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== AI Empire Status Dashboard ==="
echo "Date: $(date)"
echo ""

echo "Services:"
nc -z localhost 6379 && echo -e "${GREEN}✅${NC} Redis (6379): UP" || echo -e "${RED}❌${NC} Redis (6379): DOWN"
nc -z localhost 5432 && echo -e "${GREEN}✅${NC} PostgreSQL (5432): UP" || echo -e "${RED}❌${NC} PostgreSQL (5432): DOWN"
nc -z localhost 11434 && echo -e "${GREEN}✅${NC} Ollama (11434): UP" || echo -e "${RED}❌${NC} Ollama (11434): DOWN"
nc -z localhost 18789 && echo -e "${GREEN}✅${NC} OpenClaw (18789): UP" || echo -e "${RED}❌${NC} OpenClaw (18789): DOWN"
nc -z localhost 8888 && echo -e "${GREEN}✅${NC} Atomic Reactor (8888): UP" || echo -e "${RED}❌${NC} Atomic Reactor (8888): DOWN"
nc -z localhost 3500 && echo -e "${GREEN}✅${NC} CRM (3500): UP" || echo -e "${RED}❌${NC} CRM (3500): DOWN"

echo ""
echo "Resources:"
CPU=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
echo "CPU: ${CPU}%"
RAM=$(top -l 1 | grep "PhysMem" | awk '{print $2}' | sed 's/M//')
echo "RAM: ${RAM}MB used"
DISK=$(df -h / | tail -1 | awk '{print $4}')
echo "Disk: $DISK free"

echo ""
echo "✅ Dashboard complete"
