#!/bin/bash
# ══════════════════════════════════════════════════════════════
# AI EMPIRE — Google Cloud Deployment Script
# ══════════════════════════════════════════════════════════════
# Deploys the entire Empire system to Google Cloud.
# Account: mauricepfeiferai@gmail.com
# Project: ai-empire-486415
#
# Usage:
#   ./cloud/deploy.sh          → Full deployment
#   ./cloud/deploy.sh build    → Build container only
#   ./cloud/deploy.sh push     → Push to registry
#   ./cloud/deploy.sh run      → Deploy to Cloud Run
#   ./cloud/deploy.sh sync     → Sync data to cloud
#   ./cloud/deploy.sh infra    → Setup infrastructure (Terraform)
# ══════════════════════════════════════════════════════════════

set -e

PROJECT_ID="ai-empire-486415"
REGION="europe-west4"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/empire"
IMAGE="${REGISTRY}/api:latest"
SERVICE="empire-api"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info() { echo -e "${CYAN}→${NC} $1"; }
ok()   { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; }
head() { echo -e "\n${BOLD}═══ $1 ═══${NC}\n"; }

# ─── Pre-flight checks ───────────────────────────────────────

check_prereqs() {
    head "PRE-FLIGHT CHECK"

    # gcloud
    if command -v gcloud &>/dev/null; then
        ok "gcloud CLI installed"
    else
        fail "gcloud not found. Install: brew install google-cloud-sdk"
        exit 1
    fi

    # docker or podman
    if command -v docker &>/dev/null; then
        ok "Docker available"
        CONTAINER_CMD="docker"
    elif command -v podman &>/dev/null; then
        ok "Podman available"
        CONTAINER_CMD="podman"
    else
        fail "Docker or Podman needed. Install: brew install podman"
        exit 1
    fi

    # terraform (optional)
    if command -v terraform &>/dev/null; then
        ok "Terraform available"
    else
        info "Terraform not found (optional). Install: brew install terraform"
    fi

    # Check auth
    ACCOUNT=$(gcloud config get-value account 2>/dev/null)
    if [ -n "$ACCOUNT" ]; then
        ok "Authenticated as: $ACCOUNT"
    else
        info "Not authenticated. Running: gcloud auth login"
        gcloud auth login
    fi

    # Set project
    gcloud config set project "$PROJECT_ID" 2>/dev/null
    ok "Project: $PROJECT_ID"
    ok "Region: $REGION"
}

# ─── Build Container ─────────────────────────────────────────

build() {
    head "BUILD CONTAINER"

    cd "$(dirname "$0")/.."
    info "Building from: $(pwd)"

    $CONTAINER_CMD build -f cloud/Dockerfile -t "$IMAGE" .
    ok "Image built: $IMAGE"
}

# ─── Push to Registry ────────────────────────────────────────

push() {
    head "PUSH TO REGISTRY"

    # Create registry if not exists
    gcloud artifacts repositories describe empire \
        --location="$REGION" 2>/dev/null || \
    gcloud artifacts repositories create empire \
        --repository-format=docker \
        --location="$REGION" \
        --description="AI Empire" 2>/dev/null

    # Configure Docker auth
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

    $CONTAINER_CMD push "$IMAGE"
    ok "Pushed: $IMAGE"
}

# ─── Deploy to Cloud Run ─────────────────────────────────────

deploy_run() {
    head "DEPLOY TO CLOUD RUN"

    gcloud run deploy "$SERVICE" \
        --image="$IMAGE" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory=4Gi \
        --cpu=2 \
        --min-instances=0 \
        --max-instances=3 \
        --port=8080 \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,OLLAMA_BASE_URL=http://localhost:11434"

    URL=$(gcloud run services describe "$SERVICE" --region="$REGION" --format="value(status.url)")
    ok "Deployed!"
    echo ""
    echo -e "  ${BOLD}API URL: ${CYAN}$URL${NC}"
    echo -e "  ${BOLD}Health:  ${CYAN}$URL/health${NC}"
    echo -e "  ${BOLD}Status:  ${CYAN}$URL/status${NC}"
    echo -e "  ${BOLD}Ask AI:  ${CYAN}curl -X POST '$URL/ask?prompt=Hello'${NC}"
    echo ""
}

# ─── Sync Data to Cloud ──────────────────────────────────────

sync_data() {
    head "SYNC DATA TO CLOUD"
    BUCKET="${PROJECT_ID}-empire-data"

    # Create bucket if not exists
    gsutil ls "gs://$BUCKET" 2>/dev/null || \
    gsutil mb -l "$REGION" "gs://$BUCKET"

    # Sync empire_data
    cd "$(dirname "$0")/.."
    info "Syncing empire_data/ → gs://$BUCKET/empire_data/"
    gsutil -m rsync -r empire_data/ "gs://$BUCKET/empire_data/"

    # Sync knowledge store
    info "Syncing antigravity/_knowledge/ → gs://$BUCKET/knowledge/"
    gsutil -m rsync -r antigravity/_knowledge/ "gs://$BUCKET/knowledge/"

    # Sync products
    info "Syncing products/ → gs://$BUCKET/products/"
    gsutil -m rsync -r products/ "gs://$BUCKET/products/"

    ok "Data synced to gs://$BUCKET"
}

# ─── Setup Infrastructure (Terraform) ────────────────────────

setup_infra() {
    head "INFRASTRUCTURE SETUP (Terraform)"

    cd "$(dirname "$0")/terraform"

    if ! command -v terraform &>/dev/null; then
        fail "Terraform not installed. Install: brew install terraform"
        exit 1
    fi

    terraform init
    terraform plan -out=tfplan
    echo ""
    read -p "Apply this plan? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        terraform apply tfplan
        ok "Infrastructure deployed!"
    else
        info "Aborted."
    fi
}

# ─── Main ─────────────────────────────────────────────────────

CMD="${1:-full}"

case "$CMD" in
    build)
        check_prereqs
        build
        ;;
    push)
        check_prereqs
        push
        ;;
    run)
        check_prereqs
        deploy_run
        ;;
    sync)
        check_prereqs
        sync_data
        ;;
    infra)
        check_prereqs
        setup_infra
        ;;
    full)
        check_prereqs
        build
        push
        deploy_run
        sync_data
        ok "FULL DEPLOYMENT COMPLETE!"
        ;;
    *)
        echo "Usage: $0 {build|push|run|sync|infra|full}"
        exit 1
        ;;
esac
