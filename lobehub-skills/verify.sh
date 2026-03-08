#!/bin/bash
# LobeHub Skills Verification Script
# Validates all skills, configs, and deployment readiness

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  LobeHub Skills Verification v1.0.0${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

check_file() {
  local file=$1
  local name=$2
  if [ -f "$file" ]; then
    echo -e "  ${GREEN}✓${NC} $name"
    ((PASS++))
  else
    echo -e "  ${RED}✗${NC} $name (MISSING)"
    ((FAIL++))
  fi
}

check_dir() {
  local dir=$1
  local name=$2
  if [ -d "$dir" ]; then
    echo -e "  ${GREEN}✓${NC} $name"
    ((PASS++))
  else
    echo -e "  ${RED}✗${NC} $name (MISSING)"
    ((FAIL++))
  fi
}

# Check configuration files
echo -e "${BLUE}[1] Configuration Files${NC}"
check_file "$SCRIPT_DIR/lobehub.config.json" "LobeHub Config"
check_file "$SCRIPT_DIR/skills-registry.json" "Skills Registry"
check_file "$SCRIPT_DIR/server-integration.yaml" "Server Integration"
check_file "$SCRIPT_DIR/README.md" "Documentation"
echo ""

# Check scripts
echo -e "${BLUE}[2] Deployment Scripts${NC}"
check_file "$SCRIPT_DIR/deploy.sh" "Deploy Script"
check_file "$SCRIPT_DIR/verify.sh" "Verify Script"
echo ""

# Check all 17 skill manifests
echo -e "${BLUE}[3] Skill Manifests (17 Skills)${NC}"
SKILLS=(
  "nucleus" "legal-timeline" "legal-evidence" "legal-claims" "legal-opponent"
  "legal-caselaw" "legal-risk" "legal-settlement" "legal-summary" "legal-consistency"
  "legal-drafting" "legal-warroom" "sales-leadgen" "marketing-offers" "data-ops"
  "research-tools" "ops-router"
)

for skill in "${SKILLS[@]}"; do
  check_file "$PROJECT_ROOT/.claude/skills/$skill/SKILL.md" "$skill"
done
echo ""

# Validate JSON files
echo -e "${BLUE}[4] JSON Validation${NC}"
if command -v jq &> /dev/null; then
  if jq empty "$SCRIPT_DIR/lobehub.config.json" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} lobehub.config.json (valid JSON)"
    ((PASS++))
  else
    echo -e "  ${RED}✗${NC} lobehub.config.json (invalid JSON)"
    ((FAIL++))
  fi
  
  if jq empty "$SCRIPT_DIR/skills-registry.json" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} skills-registry.json (valid JSON)"
    ((PASS++))
  else
    echo -e "  ${RED}✗${NC} skills-registry.json (invalid JSON)"
    ((FAIL++))
  fi
else
  echo -e "  ${YELLOW}⚠${NC} jq not installed, skipping JSON validation"
fi
echo ""

# Check git status
echo -e "${BLUE}[5] Git Status${NC}"
if git rev-parse --git-dir > /dev/null 2>&1; then
  echo -e "  ${GREEN}✓${NC} Git repository detected"
  ((PASS++))
  
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
  if [ "$CURRENT_BRANCH" = "claude/setup-lobehub-skills-3xEMa" ]; then
    echo -e "  ${GREEN}✓${NC} On correct branch (claude/setup-lobehub-skills-3xEMa)"
    ((PASS++))
  else
    echo -e "  ${YELLOW}⚠${NC} On branch: $CURRENT_BRANCH"
  fi
else
  echo -e "  ${RED}✗${NC} Not a git repository"
  ((FAIL++))
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "Checks Passed:  ${GREEN}$PASS${NC}"
echo -e "Checks Failed:  ${RED}$FAIL${NC}"

if [ $FAIL -eq 0 ]; then
  echo -e "\n${GREEN}✓ All checks passed! Ready for deployment.${NC}"
  echo -e "\nNext steps:"
  echo "  1. Review: cat README.md"
  echo "  2. Deploy: bash deploy.sh"
  echo "  3. Push: git push origin claude/setup-lobehub-skills-3xEMa"
  exit 0
else
  echo -e "\n${RED}✗ Some checks failed. Please fix the issues above.${NC}"
  exit 1
fi
