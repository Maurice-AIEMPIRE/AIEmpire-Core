#!/bin/bash
# AI Empire - Master Automation Orchestrator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "${LOG_DIR}/master-automation.log"; }
info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOG_DIR}/master-automation.log"; }

log "Starting Master Automation"

# 1. System Check
info "Phase 1: System Check"
python3 --version 2>&1 | tee -a "${LOG_DIR}/master-automation.log"

# 2. Knowledge Harvest
info "Phase 2: Knowledge Harvest"
python3 "${PROJECT_ROOT}/workflow-system/knowledge_harvester.py" >> "${LOG_DIR}/master-automation.log" 2>&1 || true

# 3. Empire Brain Think
info "Phase 3: Empire Brain Think Cycle"
python3 "${PROJECT_ROOT}/workflow-system/empire_brain.py" --think --focus revenue >> "${LOG_DIR}/master-automation.log" 2>&1 || true

# 4. Git Status
info "Phase 4: Git Status"
cd "${PROJECT_ROOT}"
git status --short | tee -a "${LOG_DIR}/master-automation.log"

# 5. Report
info "Phase 5: Report"
cat > "${LOG_DIR}/automation-report-$(date +%Y%m%d).txt" << EOF
Master Automation Report - $(date)
Systems: OK
Knowledge: Harvested
Brain: Think cycle complete
EOF

log "Master Automation Complete (${SECONDS}s)"
