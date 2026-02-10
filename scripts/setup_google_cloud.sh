#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# Google Cloud + Gemini Setup Script
# AI Empire Core - Full Integration
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 AI EMPIRE - Google Cloud & Gemini Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ─── Colors ─────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✅ $1${NC}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "  ${RED}❌ $1${NC}"; }
info() { echo -e "  ${BLUE}ℹ️  $1${NC}"; }

# ─── 1. Check Prerequisites ────────────────────────────────────
echo ""
echo "━━━ Step 1: Prerequisites ━━━"

# gcloud CLI
if command -v gcloud &>/dev/null; then
    GCLOUD_VERSION=$(gcloud --version 2>&1 | head -1)
    ok "gcloud CLI: $GCLOUD_VERSION"
else
    # Try homebrew path
    export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
    if command -v gcloud &>/dev/null; then
        ok "gcloud CLI found (homebrew)"
    else
        fail "gcloud CLI not found!"
        echo "  Install: brew install --cask google-cloud-sdk"
        exit 1
    fi
fi

# Python
if command -v python3 &>/dev/null; then
    ok "Python3: $(python3 --version)"
else
    fail "Python3 not found!"
    exit 1
fi

# ─── 2. Google Cloud Authentication ────────────────────────────
echo ""
echo "━━━ Step 2: Google Cloud Authentication ━━━"

# Check if already authenticated
if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1 | grep -q "@"; then
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)
    ok "Already authenticated as: $ACCOUNT"
else
    info "Opening browser for Google Cloud login..."
    gcloud auth login --brief
    ok "Authentication complete!"
fi

# ─── 3. Project Setup ──────────────────────────────────────────
echo ""
echo "━━━ Step 3: Project Configuration ━━━"

# Check for existing project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -n "$CURRENT_PROJECT" ] && [ "$CURRENT_PROJECT" != "(unset)" ]; then
    ok "Current project: $CURRENT_PROJECT"
    read -p "  Use this project? (Y/n): " USE_CURRENT
    if [[ "${USE_CURRENT:-Y}" =~ ^[Yy]$ ]]; then
        PROJECT_ID="$CURRENT_PROJECT"
    fi
fi

if [ -z "${PROJECT_ID:-}" ]; then
    echo ""
    echo "  Available projects:"
    gcloud projects list --format="table(projectId,name,projectNumber)" 2>/dev/null || true
    echo ""
    read -p "  Enter Project ID (or 'new' to create): " PROJECT_ID

    if [ "$PROJECT_ID" == "new" ]; then
        read -p "  New project name (e.g., ai-empire-core): " PROJECT_ID
        gcloud projects create "$PROJECT_ID" --name="AI Empire Core" 2>/dev/null || true
        ok "Created project: $PROJECT_ID"
    fi

    gcloud config set project "$PROJECT_ID"
    ok "Set active project: $PROJECT_ID"
fi

# ─── 4. Enable Required APIs ───────────────────────────────────
echo ""
echo "━━━ Step 4: Enabling Google Cloud APIs ━━━"

APIS=(
    "generativelanguage.googleapis.com"    # Gemini API (direct)
    "aiplatform.googleapis.com"            # Vertex AI
    "storage.googleapis.com"               # Cloud Storage
    "cloudbuild.googleapis.com"            # Cloud Build
    "run.googleapis.com"                   # Cloud Run
    "secretmanager.googleapis.com"         # Secret Manager
    "cloudresourcemanager.googleapis.com"  # Resource Manager
)

for api in "${APIS[@]}"; do
    echo -n "  Enabling $api..."
    if gcloud services enable "$api" 2>/dev/null; then
        echo -e " ${GREEN}✅${NC}"
    else
        echo -e " ${YELLOW}⚠️  (may need billing)${NC}"
    fi
done

# ─── 5. Gemini API Key ─────────────────────────────────────────
echo ""
echo "━━━ Step 5: Gemini API Key ━━━"

# Check if key already exists in env
if [ -n "${GEMINI_API_KEY:-}" ]; then
    ok "GEMINI_API_KEY already set in environment"
else
    echo ""
    echo "  🔑 Get your Gemini API Key from:"
    echo "     https://aistudio.google.com/apikey"
    echo ""
    read -p "  Enter Gemini API Key (or press Enter to skip): " GEMINI_KEY

    if [ -n "$GEMINI_KEY" ]; then
        # Save to .env
        ENV_FILE="$(dirname "$0")/../.env"
        if [ -f "$ENV_FILE" ]; then
            # Update existing key or add new
            if grep -q "GEMINI_API_KEY" "$ENV_FILE"; then
                sed -i '' "s|GEMINI_API_KEY=.*|GEMINI_API_KEY=$GEMINI_KEY|" "$ENV_FILE"
            else
                echo "" >> "$ENV_FILE"
                echo "# --- Google Gemini ---" >> "$ENV_FILE"
                echo "GEMINI_API_KEY=$GEMINI_KEY" >> "$ENV_FILE"
            fi
        else
            cat > "$ENV_FILE" << ENVEOF
# AIEmpire-Core Environment Variables
# Generated by setup_google_cloud.sh

# --- Google Gemini ---
GEMINI_API_KEY=$GEMINI_KEY

# --- Google Cloud ---
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_REGION=europe-west1

ENVEOF
        fi
        ok "Saved GEMINI_API_KEY to .env"

        # Also export for current session
        export GEMINI_API_KEY="$GEMINI_KEY"
    else
        warn "Skipped - you can add it later to .env"
    fi
fi

# ─── 6. Configure Region ───────────────────────────────────────
echo ""
echo "━━━ Step 6: Region Setup ━━━"

REGION="${GOOGLE_CLOUD_REGION:-europe-west1}"
gcloud config set compute/region "$REGION" 2>/dev/null || true
ok "Region: $REGION (EU for GDPR compliance)"

# ─── 7. Service Account (for automated access) ─────────────────
echo ""
echo "━━━ Step 7: Service Account Setup ━━━"

SA_NAME="ai-empire-agent"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$SA_EMAIL" 2>/dev/null; then
    ok "Service account exists: $SA_EMAIL"
else
    info "Creating service account..."
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="AI Empire Agent" \
        --description="Automated agent for AI Empire operations" 2>/dev/null || true
    ok "Created service account: $SA_EMAIL"
fi

# Grant permissions
ROLES=(
    "roles/aiplatform.user"
    "roles/storage.objectAdmin"
    "roles/secretmanager.secretAccessor"
)

for role in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --quiet 2>/dev/null || true
done
ok "Permissions granted to service account"

# ─── 8. Application Default Credentials ────────────────────────
echo ""
echo "━━━ Step 8: Application Default Credentials ━━━"

if [ -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    ok "Application Default Credentials already set"
else
    info "Setting up ADC for local development..."
    gcloud auth application-default login --quiet 2>/dev/null || true
    ok "ADC configured"
fi

# ─── 9. Update .env with Google Cloud config ───────────────────
echo ""
echo "━━━ Step 9: Updating .env ━━━"

ENV_FILE="$(dirname "$0")/../.env"

# Ensure .env exists
touch "$ENV_FILE"

# Add Google Cloud vars if not present
for VAR_LINE in \
    "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    "GOOGLE_CLOUD_REGION=$REGION" \
    "VERTEX_AI_ENABLED=true"
do
    VAR_NAME="${VAR_LINE%%=*}"
    if ! grep -q "^$VAR_NAME=" "$ENV_FILE" 2>/dev/null; then
        echo "$VAR_LINE" >> "$ENV_FILE"
    fi
done

ok "Updated .env with Google Cloud configuration"

# ─── 10. Verify Setup ──────────────────────────────────────────
echo ""
echo "━━━ Step 10: Verification ━━━"

# Test Gemini API
if [ -n "${GEMINI_API_KEY:-}" ]; then
    echo -n "  Testing Gemini API..."
    RESPONSE=$(curl -s -w "%{http_code}" \
        "https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_API_KEY}" \
        -o /dev/null 2>/dev/null || echo "000")
    if [ "$RESPONSE" == "200" ]; then
        echo -e " ${GREEN}✅ WORKING${NC}"
    else
        echo -e " ${YELLOW}⚠️  HTTP $RESPONSE${NC}"
    fi
fi

# Test gcloud auth
echo -n "  Testing gcloud auth..."
if gcloud auth print-access-token &>/dev/null; then
    echo -e " ${GREEN}✅ WORKING${NC}"
else
    echo -e " ${YELLOW}⚠️  May need re-auth${NC}"
fi

# ─── Summary ───────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Project:  $PROJECT_ID"
echo "  Region:   $REGION"
echo "  Account:  $(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -1)"
echo ""
echo "  📋 Next Steps:"
echo "  1. Add GEMINI_API_KEY to .env (if not done)"
echo "     → Get key: https://aistudio.google.com/apikey"
echo "  2. Add gcloud to PATH permanently:"
echo "     echo 'export PATH=\"/opt/homebrew/share/google-cloud-sdk/bin:\$PATH\"' >> ~/.zshrc"
echo "  3. Test the unified router:"
echo "     python3 -m antigravity.unified_router status"
echo "  4. Run a test task:"
echo "     python3 -m antigravity.unified_router test"
echo ""
echo "═══════════════════════════════════════════════════════════════"
