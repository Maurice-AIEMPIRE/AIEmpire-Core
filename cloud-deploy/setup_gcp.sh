#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# AIEmpire-Core — Google Cloud Platform Full Setup
# ═══════════════════════════════════════════════════════════════
# Setzt das komplette System parallel auf GCP auf:
#   - Cloud Run Services (Empire API, CRM, Atomic Reactor)
#   - Cloud SQL (PostgreSQL)
#   - Memorystore (Redis)
#   - Cloud Storage (State, Artifacts, Gold Nuggets)
#   - Secret Manager (API Keys)
#   - Cloud Build (CI/CD)
#   - Artifact Registry (Docker Images)
#   - Cloud Scheduler (Cron Jobs)
#   - VPC + Cloud NAT (Networking)
#
# Usage:
#   ./setup_gcp.sh                    # Full setup
#   ./setup_gcp.sh --project-only     # Just create project
#   ./setup_gcp.sh --services-only    # Just deploy services
#   ./setup_gcp.sh --status           # Check deployment status
# ═══════════════════════════════════════════════════════════════

# ─── Configuration ──────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-aiempire-core}"
REGION="${GCP_REGION:-europe-west1}"
ZONE="${GCP_ZONE:-europe-west1-b}"
BILLING_ACCOUNT="${GCP_BILLING_ACCOUNT:-}"
REPO_NAME="aiempire-core"
NETWORK_NAME="empire-vpc"
SUBNET_NAME="empire-subnet"

# Service names
SVC_EMPIRE_API="empire-api"
SVC_CRM="empire-crm"
SVC_REACTOR="atomic-reactor"
SVC_OPENCLAW="openclaw-agent"

# Database
DB_INSTANCE="empire-db"
DB_NAME="empire"
DB_USER="empire_admin"
DB_TIER="db-f1-micro"  # Smallest (cost: ~$7/mo) — upgrade later

# Redis
REDIS_INSTANCE="empire-redis"
REDIS_TIER="BASIC"
REDIS_SIZE="1"  # 1 GB

# Storage buckets
BUCKET_STATE="${PROJECT_ID}-state"
BUCKET_ARTIFACTS="${PROJECT_ID}-artifacts"
BUCKET_GOLD="${PROJECT_ID}-gold-nuggets"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; }
info() { echo -e "${BLUE}[i]${NC} $*"; }

# ─── Pre-flight Checks ─────────────────────────────────────────
preflight() {
    echo "═══════════════════════════════════════════════════════"
    echo "  AIEmpire-Core — Google Cloud Setup"
    echo "═══════════════════════════════════════════════════════"
    echo

    # Check gcloud
    if ! command -v gcloud &>/dev/null; then
        err "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    log "gcloud CLI found: $(gcloud version 2>/dev/null | head -1)"

    # Check docker
    if ! command -v docker &>/dev/null; then
        warn "Docker not found — Cloud Build will handle container builds"
    else
        log "Docker found: $(docker --version)"
    fi

    # Check auth
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || true)
    if [ -z "$ACCOUNT" ]; then
        warn "Not logged in. Running gcloud auth login..."
        gcloud auth login
    else
        log "Authenticated as: $ACCOUNT"
    fi
}

# ─── 1. Project Setup ──────────────────────────────────────────
setup_project() {
    info "Setting up GCP project: $PROJECT_ID"

    # Create project if it doesn't exist
    if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
        gcloud projects create "$PROJECT_ID" --name="AI Empire Core"
        log "Project created: $PROJECT_ID"
    else
        log "Project exists: $PROJECT_ID"
    fi

    gcloud config set project "$PROJECT_ID"

    # Link billing (required for most services)
    if [ -n "$BILLING_ACCOUNT" ]; then
        gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT"
        log "Billing linked"
    else
        warn "No billing account set. Set GCP_BILLING_ACCOUNT env var."
        warn "List accounts: gcloud billing accounts list"
    fi
}

# ─── 2. Enable APIs ────────────────────────────────────────────
enable_apis() {
    info "Enabling required APIs..."

    APIS=(
        "run.googleapis.com"                # Cloud Run
        "cloudbuild.googleapis.com"         # Cloud Build
        "artifactregistry.googleapis.com"   # Container Registry
        "sqladmin.googleapis.com"           # Cloud SQL
        "redis.googleapis.com"              # Memorystore Redis
        "secretmanager.googleapis.com"      # Secret Manager
        "cloudscheduler.googleapis.com"     # Cloud Scheduler
        "compute.googleapis.com"            # Compute Engine (VPC)
        "vpcaccess.googleapis.com"          # Serverless VPC Access
        "servicenetworking.googleapis.com"  # Service Networking
        "storage.googleapis.com"            # Cloud Storage
        "logging.googleapis.com"            # Cloud Logging
        "monitoring.googleapis.com"         # Cloud Monitoring
        "aiplatform.googleapis.com"         # Vertex AI (Gemini)
    )

    gcloud services enable "${APIS[@]}" --project="$PROJECT_ID"
    log "All APIs enabled"
}

# ─── 3. Networking ──────────────────────────────────────────────
setup_networking() {
    info "Setting up VPC network..."

    # Create VPC
    if ! gcloud compute networks describe "$NETWORK_NAME" --project="$PROJECT_ID" &>/dev/null; then
        gcloud compute networks create "$NETWORK_NAME" \
            --project="$PROJECT_ID" \
            --subnet-mode=custom
        log "VPC created: $NETWORK_NAME"
    fi

    # Create subnet
    if ! gcloud compute networks subnets describe "$SUBNET_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        gcloud compute networks subnets create "$SUBNET_NAME" \
            --project="$PROJECT_ID" \
            --network="$NETWORK_NAME" \
            --region="$REGION" \
            --range="10.0.0.0/24"
        log "Subnet created: $SUBNET_NAME"
    fi

    # Create VPC connector for Cloud Run → Cloud SQL/Redis
    if ! gcloud compute networks vpc-access connectors describe empire-connector --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        gcloud compute networks vpc-access connectors create empire-connector \
            --project="$PROJECT_ID" \
            --region="$REGION" \
            --network="$NETWORK_NAME" \
            --range="10.8.0.0/28" \
            --min-instances=2 \
            --max-instances=3
        log "VPC connector created"
    fi

    # Allocate IP range for private services
    if ! gcloud compute addresses describe empire-private-ip --global --project="$PROJECT_ID" &>/dev/null; then
        gcloud compute addresses create empire-private-ip \
            --project="$PROJECT_ID" \
            --global \
            --purpose=VPC_PEERING \
            --prefix-length=16 \
            --network="$NETWORK_NAME"

        gcloud services vpc-peerings connect \
            --project="$PROJECT_ID" \
            --service=servicenetworking.googleapis.com \
            --ranges=empire-private-ip \
            --network="$NETWORK_NAME"
        log "Private service connection established"
    fi
}

# ─── 4. Artifact Registry ──────────────────────────────────────
setup_registry() {
    info "Setting up Artifact Registry..."

    if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        gcloud artifacts repositories create "$REPO_NAME" \
            --project="$PROJECT_ID" \
            --repository-format=docker \
            --location="$REGION" \
            --description="AI Empire Core container images"
        log "Artifact Registry created: $REPO_NAME"
    fi

    # Configure Docker auth
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
    log "Docker auth configured"
}

# ─── 5. Secret Manager ─────────────────────────────────────────
setup_secrets() {
    info "Setting up Secret Manager..."

    SECRETS=(
        "GEMINI_API_KEY"
        "MOONSHOT_API_KEY"
        "ANTHROPIC_API_KEY"
        "OPENAI_API_KEY"
        "GUMROAD_ACCESS_TOKEN"
        "TWITTER_BEARER_TOKEN"
        "TELEGRAM_BOT_TOKEN"
        "N8N_ENCRYPTION_KEY"
        "DB_PASSWORD"
        "REDIS_PASSWORD"
    )

    for secret in "${SECRETS[@]}"; do
        if ! gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
            # Create secret with placeholder
            echo -n "CHANGE_ME" | gcloud secrets create "$secret" \
                --project="$PROJECT_ID" \
                --replication-policy="automatic" \
                --data-file=-
            warn "Secret created with placeholder: $secret — UPDATE IT!"
        else
            log "Secret exists: $secret"
        fi
    done

    echo
    warn "Update secrets with real values:"
    warn "  echo -n 'your-key' | gcloud secrets versions add SECRET_NAME --data-file=-"
}

# ─── 6. Cloud SQL (PostgreSQL) ─────────────────────────────────
setup_database() {
    info "Setting up Cloud SQL PostgreSQL..."

    if ! gcloud sql instances describe "$DB_INSTANCE" --project="$PROJECT_ID" &>/dev/null; then
        # Generate random password
        DB_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)

        gcloud sql instances create "$DB_INSTANCE" \
            --project="$PROJECT_ID" \
            --database-version=POSTGRES_15 \
            --tier="$DB_TIER" \
            --region="$REGION" \
            --network="projects/$PROJECT_ID/global/networks/$NETWORK_NAME" \
            --no-assign-ip \
            --storage-type=SSD \
            --storage-size=10GB \
            --storage-auto-increase \
            --backup-start-time=03:00 \
            --availability-type=zonal

        # Create database
        gcloud sql databases create "$DB_NAME" \
            --instance="$DB_INSTANCE" \
            --project="$PROJECT_ID"

        # Create user
        gcloud sql users create "$DB_USER" \
            --instance="$DB_INSTANCE" \
            --project="$PROJECT_ID" \
            --password="$DB_PASSWORD"

        # Store password in Secret Manager
        echo -n "$DB_PASSWORD" | gcloud secrets versions add DB_PASSWORD \
            --project="$PROJECT_ID" \
            --data-file=-

        log "Cloud SQL created: $DB_INSTANCE"
        log "Database: $DB_NAME, User: $DB_USER"
        info "Password stored in Secret Manager: DB_PASSWORD"
    else
        log "Cloud SQL exists: $DB_INSTANCE"
    fi

    # Get connection info
    DB_IP=$(gcloud sql instances describe "$DB_INSTANCE" \
        --project="$PROJECT_ID" \
        --format="value(ipAddresses[0].ipAddress)" 2>/dev/null || echo "pending")
    info "Database IP: $DB_IP"
}

# ─── 7. Memorystore Redis ──────────────────────────────────────
setup_redis() {
    info "Setting up Memorystore Redis..."

    if ! gcloud redis instances describe "$REDIS_INSTANCE" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        gcloud redis instances create "$REDIS_INSTANCE" \
            --project="$PROJECT_ID" \
            --region="$REGION" \
            --size="$REDIS_SIZE" \
            --tier="$REDIS_TIER" \
            --network="projects/$PROJECT_ID/global/networks/$NETWORK_NAME" \
            --redis-version=redis_7_0 \
            --display-name="Empire Redis"

        log "Redis created: $REDIS_INSTANCE"
    else
        log "Redis exists: $REDIS_INSTANCE"
    fi

    REDIS_HOST=$(gcloud redis instances describe "$REDIS_INSTANCE" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(host)" 2>/dev/null || echo "pending")
    REDIS_PORT=$(gcloud redis instances describe "$REDIS_INSTANCE" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(port)" 2>/dev/null || echo "6379")
    info "Redis: $REDIS_HOST:$REDIS_PORT"
}

# ─── 8. Cloud Storage ──────────────────────────────────────────
setup_storage() {
    info "Setting up Cloud Storage buckets..."

    for BUCKET in "$BUCKET_STATE" "$BUCKET_ARTIFACTS" "$BUCKET_GOLD"; do
        if ! gcloud storage buckets describe "gs://$BUCKET" --project="$PROJECT_ID" &>/dev/null; then
            gcloud storage buckets create "gs://$BUCKET" \
                --project="$PROJECT_ID" \
                --location="$REGION" \
                --default-storage-class=STANDARD \
                --uniform-bucket-level-access
            log "Bucket created: gs://$BUCKET"
        else
            log "Bucket exists: gs://$BUCKET"
        fi
    done

    # Set lifecycle (auto-delete old state files after 30 days)
    cat > /tmp/lifecycle.json << 'LIFECYCLE'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30, "matchesPrefix": ["state/old/"]}
      }
    ]
  }
}
LIFECYCLE
    gcloud storage buckets update "gs://$BUCKET_STATE" --lifecycle-file=/tmp/lifecycle.json --project="$PROJECT_ID" 2>/dev/null || true
}

# ─── 9. Build & Deploy Services ────────────────────────────────
build_and_deploy() {
    info "Building and deploying services..."

    IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

    # Get database and redis connection info
    DB_IP=$(gcloud sql instances describe "$DB_INSTANCE" \
        --project="$PROJECT_ID" \
        --format="value(ipAddresses[0].ipAddress)" 2>/dev/null || echo "10.0.0.1")
    REDIS_HOST=$(gcloud redis instances describe "$REDIS_INSTANCE" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(host)" 2>/dev/null || echo "10.0.0.2")

    # Deploy Empire API (Port 3333)
    info "Deploying Empire API..."
    gcloud run deploy "$SVC_EMPIRE_API" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --source="." \
        --port=3333 \
        --memory=512Mi \
        --cpu=1 \
        --min-instances=0 \
        --max-instances=3 \
        --vpc-connector=empire-connector \
        --set-env-vars="DB_HOST=$DB_IP,DB_NAME=$DB_NAME,DB_USER=$DB_USER,REDIS_URL=redis://$REDIS_HOST:6379,ENVIRONMENT=production" \
        --set-secrets="DB_PASSWORD=DB_PASSWORD:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,MOONSHOT_API_KEY=MOONSHOT_API_KEY:latest" \
        --allow-unauthenticated \
        --command="python,-m,uvicorn,empire_api.main:app,--host,0.0.0.0,--port,3333" \
        --quiet || warn "Empire API deployment failed — check Dockerfile"

    # Deploy Atomic Reactor (Port 8888)
    info "Deploying Atomic Reactor..."
    gcloud run deploy "$SVC_REACTOR" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --source="." \
        --port=8888 \
        --memory=1Gi \
        --cpu=2 \
        --min-instances=0 \
        --max-instances=5 \
        --vpc-connector=empire-connector \
        --set-env-vars="DB_HOST=$DB_IP,REDIS_URL=redis://$REDIS_HOST:6379,ENVIRONMENT=production" \
        --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest" \
        --allow-unauthenticated \
        --quiet || warn "Atomic Reactor deployment failed"

    # Deploy CRM (Port 3500)
    info "Deploying CRM..."
    gcloud run deploy "$SVC_CRM" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --source="crm/" \
        --port=3500 \
        --memory=256Mi \
        --cpu=1 \
        --min-instances=0 \
        --max-instances=2 \
        --vpc-connector=empire-connector \
        --set-env-vars="DB_HOST=$DB_IP,REDIS_URL=redis://$REDIS_HOST:6379,NODE_ENV=production" \
        --set-secrets="DB_PASSWORD=DB_PASSWORD:latest" \
        --allow-unauthenticated \
        --quiet || warn "CRM deployment failed"
}

# ─── 10. Cloud Scheduler (Cron Jobs) ───────────────────────────
setup_scheduler() {
    info "Setting up Cloud Scheduler cron jobs..."

    # Get service URLs
    API_URL=$(gcloud run services describe "$SVC_EMPIRE_API" \
        --region="$REGION" --project="$PROJECT_ID" \
        --format="value(status.url)" 2>/dev/null || echo "https://empire-api-xxx.run.app")

    REACTOR_URL=$(gcloud run services describe "$SVC_REACTOR" \
        --region="$REGION" --project="$PROJECT_ID" \
        --format="value(status.url)" 2>/dev/null || echo "https://atomic-reactor-xxx.run.app")

    # Workflow: Every 6 hours
    gcloud scheduler jobs create http empire-workflow \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --schedule="0 */6 * * *" \
        --uri="${API_URL}/api/workflow/run" \
        --http-method=POST \
        --oidc-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
        --description="Run 5-step compound loop" \
        2>/dev/null || warn "Scheduler: empire-workflow already exists"

    # Cowork: Every 30 minutes
    gcloud scheduler jobs create http empire-cowork \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --schedule="*/30 * * * *" \
        --uri="${API_URL}/api/cowork/cycle" \
        --http-method=POST \
        --oidc-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
        --description="Cowork Observe-Plan-Act-Reflect cycle" \
        2>/dev/null || warn "Scheduler: empire-cowork already exists"

    # Gemini Sync: Every 15 minutes
    gcloud scheduler jobs create http gemini-sync \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --schedule="*/15 * * * *" \
        --uri="${API_URL}/api/gemini/sync" \
        --http-method=POST \
        --oidc-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
        --description="Gemini Mirror bidirectional sync" \
        2>/dev/null || warn "Scheduler: gemini-sync already exists"

    # Dual Brain Pulse: Every hour
    gcloud scheduler jobs create http dual-brain-pulse \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --schedule="0 * * * *" \
        --uri="${API_URL}/api/gemini/brain" \
        --http-method=POST \
        --oidc-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
        --description="Dual Brain amplification pulse" \
        2>/dev/null || warn "Scheduler: dual-brain-pulse already exists"

    # Vision Interrogator: 3x daily
    gcloud scheduler jobs create http vision-questions \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --schedule="0 8,14,20 * * *" \
        --uri="${API_URL}/api/gemini/vision" \
        --http-method=POST \
        --oidc-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
        --description="Vision interrogator - daily questions" \
        2>/dev/null || warn "Scheduler: vision-questions already exists"

    log "Scheduler jobs configured"
}

# ─── 11. Cloud Monitoring ──────────────────────────────────────
setup_monitoring() {
    info "Setting up monitoring alerts..."

    # Create notification channel (email)
    # NOTE: Replace with your email
    cat > /tmp/notification_channel.json << 'NOTIF'
{
  "type": "email",
  "displayName": "Empire Admin",
  "labels": {
    "email_address": "admin@aiempire.dev"
  }
}
NOTIF

    warn "Monitoring: Configure email in Cloud Console → Monitoring → Alerting"
    warn "Or set up PagerDuty/Slack integration for production"
}

# ─── Status Check ──────────────────────────────────────────────
check_status() {
    echo "═══════════════════════════════════════════════════════"
    echo "  AIEmpire-Core — GCP Deployment Status"
    echo "═══════════════════════════════════════════════════════"
    echo

    # Project
    info "Project: $PROJECT_ID"

    # Cloud Run services
    echo
    info "Cloud Run Services:"
    gcloud run services list --project="$PROJECT_ID" --region="$REGION" \
        --format="table(name, status.url, status.conditions[0].status)" 2>/dev/null || warn "No services found"

    # Cloud SQL
    echo
    info "Cloud SQL:"
    gcloud sql instances list --project="$PROJECT_ID" \
        --format="table(name, state, ipAddresses[0].ipAddress, settings.tier)" 2>/dev/null || warn "No databases"

    # Redis
    echo
    info "Memorystore Redis:"
    gcloud redis instances list --region="$REGION" --project="$PROJECT_ID" \
        --format="table(name, state, host, port, memorySizeGb)" 2>/dev/null || warn "No Redis instances"

    # Storage
    echo
    info "Cloud Storage:"
    gcloud storage buckets list --project="$PROJECT_ID" \
        --format="table(name, location, storageClass)" 2>/dev/null || warn "No buckets"

    # Scheduler
    echo
    info "Scheduler Jobs:"
    gcloud scheduler jobs list --location="$REGION" --project="$PROJECT_ID" \
        --format="table(name, schedule, state)" 2>/dev/null || warn "No scheduler jobs"

    # Secrets
    echo
    info "Secrets:"
    gcloud secrets list --project="$PROJECT_ID" \
        --format="table(name, createTime)" 2>/dev/null || warn "No secrets"

    echo
    echo "═══════════════════════════════════════════════════════"

    # Cost estimate
    echo
    info "Estimated monthly cost (minimum usage):"
    echo "  Cloud SQL (db-f1-micro):     ~\$7/mo"
    echo "  Memorystore Redis (1GB):     ~\$35/mo"
    echo "  Cloud Run (scale to 0):      ~\$0-5/mo"
    echo "  Cloud Storage:               ~\$1/mo"
    echo "  VPC Connector:               ~\$7/mo"
    echo "  Cloud Scheduler:             ~\$0.10/mo"
    echo "  ──────────────────────────────────"
    echo "  Total minimum:               ~\$50/mo"
    echo "  With Vertex AI (Gemini):     +\$10-50/mo"
    echo
}

# ─── Main ──────────────────────────────────────────────────────
main() {
    case "${1:-}" in
        --status)
            check_status
            exit 0
            ;;
        --project-only)
            preflight
            setup_project
            enable_apis
            exit 0
            ;;
        --services-only)
            preflight
            build_and_deploy
            exit 0
            ;;
        --help)
            echo "Usage: $0 [--status|--project-only|--services-only|--help]"
            exit 0
            ;;
    esac

    preflight
    echo

    # Full setup in order
    setup_project
    echo
    enable_apis
    echo
    setup_networking
    echo
    setup_registry
    echo
    setup_secrets
    echo
    setup_database
    echo
    setup_redis
    echo
    setup_storage
    echo
    build_and_deploy
    echo
    setup_scheduler
    echo
    setup_monitoring

    echo
    echo "═══════════════════════════════════════════════════════"
    echo "  SETUP COMPLETE!"
    echo "═══════════════════════════════════════════════════════"
    echo
    echo "Next steps:"
    echo "  1. Update secrets:  echo -n 'key' | gcloud secrets versions add SECRET_NAME --data-file=-"
    echo "  2. Check status:    $0 --status"
    echo "  3. View logs:       gcloud run logs read --project=$PROJECT_ID --region=$REGION"
    echo "  4. Setup CI/CD:     See cloud-deploy/cloudbuild.yaml"
    echo
    log "System parallel auf GCP deployed!"
}

main "$@"
