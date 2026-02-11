#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# AIEmpire-Core — Quick GCE VM Deployment
# ═══════════════════════════════════════════════════════════════
# One-command deployment to a GCE VM with everything pre-configured.
#
# Usage:
#   ./deploy_vm.sh                    # Create + deploy
#   ./deploy_vm.sh --delete           # Tear down VM
#   ./deploy_vm.sh --ssh              # SSH into VM
#   ./deploy_vm.sh --status           # Check VM status
# ═══════════════════════════════════════════════════════════════

PROJECT_ID="${GCP_PROJECT_ID:-aiempire-core}"
ZONE="${GCP_ZONE:-europe-west1-b}"
VM_NAME="empire-vm"
MACHINE_TYPE="${GCP_MACHINE_TYPE:-e2-standard-4}"  # 4 vCPU, 16GB RAM (~$100/mo)
DISK_SIZE="50GB"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }

create_vm() {
    echo "═══════════════════════════════════════════════════════"
    echo "  Creating GCE VM: $VM_NAME"
    echo "  Machine: $MACHINE_TYPE | Disk: $DISK_SIZE | Zone: $ZONE"
    echo "═══════════════════════════════════════════════════════"

    # Create VM with startup script
    gcloud compute instances create "$VM_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size="$DISK_SIZE" \
        --boot-disk-type=pd-ssd \
        --tags=http-server,https-server \
        --metadata-from-file=startup-script="${SCRIPT_DIR}/bootstrap_vm.sh" \
        --scopes=cloud-platform

    log "VM created: $VM_NAME"

    # Create firewall rules
    gcloud compute firewall-rules create allow-empire-http \
        --project="$PROJECT_ID" \
        --allow=tcp:80,tcp:443 \
        --target-tags=http-server,https-server \
        --description="Allow HTTP/HTTPS for Empire" \
        2>/dev/null || true

    gcloud compute firewall-rules create allow-empire-api \
        --project="$PROJECT_ID" \
        --allow=tcp:3333,tcp:3500,tcp:8888 \
        --target-tags=http-server \
        --source-ranges="0.0.0.0/0" \
        --description="Allow Empire API ports" \
        2>/dev/null || true

    # Wait for VM to be ready
    echo "Waiting for VM to boot..."
    sleep 30

    # Get external IP
    EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" \
        --zone="$ZONE" --project="$PROJECT_ID" \
        --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

    echo
    echo "═══════════════════════════════════════════════════════"
    echo "  VM READY"
    echo "═══════════════════════════════════════════════════════"
    echo "  IP:     $EXTERNAL_IP"
    echo "  SSH:    gcloud compute ssh $VM_NAME --zone=$ZONE"
    echo "  API:    http://$EXTERNAL_IP/api/"
    echo "  CRM:    http://$EXTERNAL_IP/crm/"
    echo "  Health: http://$EXTERNAL_IP/health"
    echo
    echo "  Bootstrap is running in background (~5 min)."
    echo "  Check progress: gcloud compute ssh $VM_NAME -- tail -f /var/log/syslog"
    echo "═══════════════════════════════════════════════════════"
}

delete_vm() {
    warn "Deleting VM: $VM_NAME"
    gcloud compute instances delete "$VM_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --quiet
    log "VM deleted"
}

ssh_vm() {
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT_ID"
}

show_status() {
    echo "═══════════════════════════════════════════════════════"
    echo "  VM Status: $VM_NAME"
    echo "═══════════════════════════════════════════════════════"

    gcloud compute instances describe "$VM_NAME" \
        --zone="$ZONE" --project="$PROJECT_ID" \
        --format="table(name, status, networkInterfaces[0].accessConfigs[0].natIP, machineType.basename(), disks[0].diskSizeGb)" \
        2>/dev/null || echo "VM not found"

    echo

    # Try to get service status via SSH
    EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" \
        --zone="$ZONE" --project="$PROJECT_ID" \
        --format="value(networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null || true)

    if [ -n "$EXTERNAL_IP" ]; then
        echo "  Health check:"
        curl -sf "http://$EXTERNAL_IP/health" 2>/dev/null | jq . || echo "  Not responding yet"
    fi

    echo "═══════════════════════════════════════════════════════"
}

# ─── Cost Estimates ─────────────────────────────────────────
show_costs() {
    echo "═══════════════════════════════════════════════════════"
    echo "  GCE VM Cost Estimates (europe-west1)"
    echo "═══════════════════════════════════════════════════════"
    echo
    echo "  Machine Types:"
    echo "    e2-micro      (2 vCPU,  1GB):  ~\$6/mo   (free tier eligible)"
    echo "    e2-small      (2 vCPU,  2GB):  ~\$13/mo"
    echo "    e2-medium     (2 vCPU,  4GB):  ~\$25/mo"
    echo "    e2-standard-2 (2 vCPU,  8GB):  ~\$49/mo"
    echo "    e2-standard-4 (4 vCPU, 16GB):  ~\$97/mo  ← RECOMMENDED"
    echo "    e2-standard-8 (8 vCPU, 32GB):  ~\$194/mo"
    echo
    echo "  SSD Disk: ~\$0.17/GB/mo (50GB = \$8.50)"
    echo "  Static IP: ~\$3/mo (if reserved)"
    echo "  Egress: First 1GB free, then \$0.12/GB"
    echo
    echo "  Spot/Preemptible VMs: 60-91% cheaper!"
    echo "    e2-standard-4 spot: ~\$29/mo (vs \$97 on-demand)"
    echo "═══════════════════════════════════════════════════════"
}

case "${1:-}" in
    --delete)  delete_vm ;;
    --ssh)     ssh_vm ;;
    --status)  show_status ;;
    --costs)   show_costs ;;
    --help)
        echo "Usage: $0 [--delete|--ssh|--status|--costs|--help]"
        echo "Default: create and deploy VM"
        ;;
    *)         create_vm ;;
esac
