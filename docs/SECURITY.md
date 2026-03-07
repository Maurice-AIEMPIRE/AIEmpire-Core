# AI EMPIRE SECURITY & THREAT MODEL

**Last Updated**: 2026-02-10
**Owner**: CLAUDE (Chief Security Officer)
**Classification**: INTERNAL (Handle with care)

---

## 🎯 SECURITY PHILOSOPHY

> **Secure-by-Default**: Every new service, script, and feature defaults to "deny" unless explicitly approved. Security is not a feature; it's a foundation.

**Three Principles**:
1. **Principle of Least Privilege**: Each service/agent has minimal permissions needed for its job
2. **Defense in Depth**: Multiple layers (network, OS, app, data)
3. **Observability First**: If we can't see it, we can't secure it

---

## 🔍 THREAT MODEL

### **ADVERSARY PROFILES**

| Profile | Capabilities | Goals | Likelihood |
|---------|-------------|-------|------------|
| **Script Kiddie** | Automated exploits, default creds | Ransomware, cryptocurrency mining | HIGH |
| **Opportunistic Attacker** | Port scanning, CVE exploits | Find + exploit unpatched services | HIGH |
| **Credential Stuffing** | Leaked password lists | Brute force accounts (API key theft) | MEDIUM |
| **Supply Chain** | Malicious dependencies, GitHub issues | Plant backdoor in code | MEDIUM |
| **Insider (Low-Risk)** | SSH access, .env file access | Steal API keys, abuse resources | LOW (Maurice trusted) |
| **Malware** | Infected script/dependency | Exfiltrate data, launch botnet | MEDIUM |
| **AI/LLM Injection** | Crafted prompts, jailbreaks | Exfiltrate secrets, generate malicious output | MEDIUM |

---

### **ATTACK SURFACES**

| Attack Vector | Current State | Risk | Mitigation |
|---------------|---------------|------|-----------|
| **Internet-facing ports** | 3333 (API), 5678 (n8n), 3000 (Grafana) | 🔴 HIGH | Firewall + VPN-only access |
| **Default credentials** | empire_pass, n8n_pass, redis_pass in docker-compose | 🔴 HIGH | Move to secrets vault |
| **No TLS/mTLS** | All local traffic unencrypted | 🔴 HIGH | Implement Traefik + mTLS |
| **Secrets in env vars** | .env file on disk (readable by all services) | 🔴 HIGH | Implement sops/age encryption |
| **API key rotation** | None (keys never expire) | 🟡 MEDIUM | Auto-rotate every 90 days |
| **Dependency vulnerabilities** | No Dependabot checks | 🟡 MEDIUM | Enable auto-scanning |
| **Container escape** | Running as root, no seccomp | 🟡 MEDIUM | Rootless Docker, seccomp profiles |
| **Prompt injection** | LLM agents accept untrusted input | 🟡 MEDIUM | Input sanitization + sandboxing |
| **CI/CD compromise** | GitHub Actions secrets not rotated | 🟡 MEDIUM | Branch protection + approval gates |
| **Database backups** | No encryption at rest | 🟡 MEDIUM | Encrypt backups (AES-256) |
| **Unauthorized agent execution** | No operator approval for high-risk tasks | 🟡 MEDIUM | Dry-run mode + manual gates |
| **DDoS** | No rate limiting per IP/user | 🟡 MEDIUM | Traefik rate limits + Cloudflare |
| **Data exfiltration** | Agents can write to any directory | 🟡 MEDIUM | Container write-only paths, audit logs |
| **SSH keys leak** | SSH key stored on disk | 🟡 MEDIUM | SSH key agent, no local storage |

---

### **ASSETS TO PROTECT**

| Asset | Value | Classification | Current Protection |
|-------|-------|-----------------|-------------------|
| **API Keys** | EUR 10K+/month (Kimi budget) | CRITICAL | .env file (🔴 weak) |
| **Database** (PostgreSQL) | All customer/lead data | CRITICAL | PostgreSQL auth (🟡 medium) |
| **Secrets** (JWT, Redis auth) | Authentication backbone | CRITICAL | .env file (🔴 weak) |
| **Agent Executions** | Code + data processing | HIGH | Docker isolation (🟡 medium) |
| **Backups** | Disaster recovery | HIGH | Local filesystem (🔴 weak) |
| **Source Code** | IP + business logic | HIGH | GitHub private repo (✅ good) |
| **Content** (80+ gold nuggets) | Business intelligence | MEDIUM | ChromaDB + RBAC (🟡 partial) |
| **CRM Data** (leads, scores) | Sales opportunity | MEDIUM | SQLite local (🔴 weak) |

---

## 🛡️ HARDENING CONTROLS

### **LAYER 1: NETWORK & PERIMETER**

#### **1.1 Default Setup (Deny-All)**
```
Internet
  ↓
[Firewall] ← BLOCK all inbound (0.0.0.0/0)
  ↓
VPN Gateway [Tailscale/WireGuard] ← Only authorized IPs
  ↓
Reverse Proxy [Traefik] ← SSL/TLS termination, rate limiting
  ↓
Docker Internal Network (172.20.0.0/24) ← Service-to-service only
```

**Implementation**:
- [ ] Enable UFW/iptables (deny inbound, allow SSH + VPN only)
- [ ] Deploy Tailscale (free tier supports 3 devices)
- [ ] Configure Traefik for mTLS + rate limiting
- [ ] Disable all services' public ports (listen on 127.0.0.1 only)

**Commands**:
```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from [TAILSCALE_IP] to any port 22
sudo ufw allow from [TAILSCALE_IP] to any port 80,443
sudo ufw enable

# Docker network isolation
docker network create --driver bridge \
  --opt "--icc=false" \
  --opt "--com.docker.network.bridge.disable_ip_masquerade=true" \
  ai-empire-net
```

---

#### **1.2 Reverse Proxy (Traefik + HTTPS)**
**Implementation**: See `/ops/traefik/docker-compose.override.yml` (to be created)

**Features**:
- Auto-SSL certificates (Let's Encrypt or self-signed + mTLS)
- Rate limiting: 100 req/min per IP
- Request logging (JSON format for audit)
- Authentication middleware (JWT validation)
- Circuit breaker (fail-fast on unhealthy backends)

---

### **LAYER 2: SECRETS MANAGEMENT**

#### **2.1 Move from .env to Encrypted Vault**

**Current**: ❌ `.env` in plaintext on disk
```
MOONSHOT_API_KEY=sk-xxxxxx
GEMINI_API_KEY=XXXX
REDIS_PASSWORD=empire_pass
DATABASE_URL=postgresql://user:password@...
```

**Proposed**: ✅ **sops + age encryption** (Open Source)

**Implementation**:
```bash
# Install sops + age
brew install sops age

# Generate age encryption key
age-keygen -o ~/.age/keys.txt

# Encrypt .env.enc (commit this, keep key safe)
sops --encrypt --age $(cat ~/.age/keys.txt | grep "public key") .env > .env.enc

# Decrypt at runtime (CI/CD + local)
export SOPS_AGE_KEY_FILE=~/.age/keys.txt
sops --decrypt .env.enc > .env.tmp  # Temporary
source .env.tmp
rm .env.tmp
```

**CI/CD Integration** (GitHub Actions):
```yaml
# In .github/workflows/deploy.yml
jobs:
  deploy:
    steps:
      - name: Decrypt secrets
        env:
          SOPS_AGE_KEY: ${{ secrets.AGE_PRIVATE_KEY }}  # Stored in GitHub Secrets
        run: |
          sops --decrypt .env.enc > .env
          docker compose up -d
      - name: Clean up
        run: shred -u .env  # Overwrite + delete
```

**Rotation Policy**:
- [ ] Rotate API keys every 90 days
- [ ] Rotate database passwords every 180 days
- [ ] Rotate age encryption key every 1 year
- [ ] Automated alerts (7 days before expiration)

---

#### **2.2 API Key Management**

**Current Problem**: API keys in .env never expire → compromised key = forever access

**Solution**:
```python
# scripts/rotate_secrets.py
#!/usr/bin/env python3
import os, json, datetime
from moonshot import MoonShotAPI

def rotate_api_keys():
    """Auto-rotate Moonshot + other API keys"""
    config = {
        'moonshot': {
            'rotate_interval_days': 90,
            'last_rotated': datetime.datetime.now().isoformat(),
        }
    }

    # Generate new key on Moonshot dashboard (manual for now)
    # TODO: Implement via API when available

    # Store in sops
    os.system("sops --encrypt .env > .env.enc")
    print("✅ Secrets rotated and encrypted")

if __name__ == '__main__':
    rotate_api_keys()
```

*Scheduled**: GitHub Actions cron (monthly check, manual approval for rotation)

---

### **LAYER 3: CONTAINER & OS HARDENING**

#### **3.1 Rootless Docker**
**Current**: Containers run as root (standard Docker Compose)
**Proposed**: Rootless Docker (containers run as unprivileged user)

```bash
# Install rootless Docker (macOS: not available; Linux: available)
# For macOS: Use Podman instead (drop-in replacement)
brew install podman

# Convert docker-compose → podman-compose
podman-compose up -d

# Set resource limits in podman-compose
services:
  empire-api:
    image: fastapi:latest
    security_opt:
      - no-new-privileges:true  # Prevent privilege escalation
    cap_drop:                    # Drop unnecessary Linux capabilities
      - ALL
    cap_add:
      - NET_BIND_SERVICE       # Minimal needed caps
      - CHOWN
    read_only: true             # Read-only filesystem (mount /tmp as rw if needed)
    tmpfs:
      - /tmp
      - /var/tmp
    networks:
      - ai-empire-net:
          ipv4_address: 172.20.0.3
```

---

#### **3.2 Container Image Security**

**Hardening Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Run as unprivileged user
RUN useradd -m -u 1000 appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

# Install deps as root, then switch user
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    chown -R appuser:appuser /app

USER appuser:appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
```

**Security Scanning**:
```bash
# Scan for vulnerabilities
trivy image --severity HIGH,CRITICAL my-fastapi-app:latest

# Generate SBOM (Software Bill of Materials)
syft my-fastapi-app:latest -o json > sbom.json

# Sign images (optional, for supply chain integrity)
cosign sign --key cosign.key my-fastapi-app:latest
```

---

#### **3.3 Runtime Security (Seccomp + AppArmor)**

**Seccomp Profile** (`/ops/security/seccomp-profile.json`):
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "archMap": [{"architecture": "SCMP_ARCH_X86_64"}],
  "syscalls": [
    {
      "name": "read",
      "action": "SCMP_ACT_ALLOW",
      "args": [{"index": 0, "value": 0, "valueTwo": 0, "op": "SCMP_CMP_EQ"}]
    },
    {"name": "write", "action": "SCMP_ACT_ALLOW"},
    {"name": "open", "action": "SCMP_ACT_ALLOW"},
    {"name": "exit", "action": "SCMP_ACT_ALLOW"},
    {"name": "exit_group", "action": "SCMP_ACT_ALLOW"}
    /* ... only safe syscalls ... */
  ]
}
```

**Apply in docker-compose**:
```yaml
services:
  empire-api:
    security_opt:
      - seccomp=./ops/security/seccomp-profile.json
```

---

### **LAYER 4: APPLICATION SECURITY**

#### **4.1 Input Validation (Prompt Injection Defense)**

**Problem**: Agents accept user input → LLM processes it → Potential to exfiltrate secrets

**Solution**: Multi-layer validation

```python
# empire_api/security.py
import re
from functools import wraps

DANGEROUS_PATTERNS = [
    r'(?i)(api_key|password|secret|token|credential)',  # Secret keywords
    r'(?i)(ignore|disregard|forget).*instruction',       # Jailbreak attempts
    r'(?i)(print|echo|output).*env',                     # Env var exfiltration
]

def validate_user_input(input_text: str) -> bool:
    """Block suspicious inputs"""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, input_text):
            log_security_event("PROMPT_INJECTION_ATTEMPT", input_text)
            return False
    return True

@app.post("/api/action")
def execute_action(request: ActionRequest):
    # 1. Validate input
    if not validate_user_input(request.prompt):
        return {"error": "Invalid input detected"}, 400

    # 2. Log action (audit trail)
    log_action("USER_ACTION", user_id=request.user_id, action=request.prompt)

    # 3. Run in sandbox (no direct shell access)
    result = orchestrator.execute_safe(request.prompt)

    # 4. Sanitize output (no secrets leaked)
    result = sanitize_output(result)

    return result

def sanitize_output(text: str) -> str:
    """Remove potential secrets from output"""
    # Redact API keys (format: sk-xxxx or similar)
    text = re.sub(r'sk-[A-Za-z0-9]{20,}', 'sk-[REDACTED]', text)
    # Redact database URLs
    text = re.sub(r'postgresql://\S+', 'postgresql://[REDACTED]', text)
    return text
```

---

#### **4.2 Agent Sandboxing**

**Problem**: Agents can execute arbitrary code (tool use)

**Solution**: Allowlist + capability dropping

```python
# agents/base_agent.py
class SafeAgent:
    ALLOWED_COMMANDS = [
        'curl',         # HTTP requests (no pipe to bash)
        'jq',          # JSON parsing
        'tar',         # Archive (no zips that can escape)
        'ls',          # Safe file listing
        'wc',          # Word count
    ]

    BLOCKED_COMMAND
S = [
        'rm',          # Dangerous deletion
        'sudo',        # Privilege escalation
        'ssh',         # Lateral movement
        'docker',      # Container escape risk
        'systemctl',   # System control
    ]

    def execute_tool(self, tool_name: str, args: list) -> str:
        # 1. Check allowlist
        if tool_name not in self.ALLOWED_COMMANDS:
            log_security_event("TOOL_BLOCKED", tool=tool_name)
            return "Tool not allowed"

        # 2. Validate args (no pipe/redirection)
        for arg in args:
            if any(char in arg for char in ['|', '>', '<', ';', '&', '$']):
                log_security_event("SHELL_INJECTION_ATTEMPT", args=args)
                return "Invalid arguments"

        # 3. Run in sandbox (timeout, no network)
        try:
            result = subprocess.run(
                [tool_name] + args,
                timeout=30,
                capture_output=True,
                text=True,
                # No shell=True (prevents shell injection)
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "Tool execution timeout"
        except Exception as e:
            log_security_event("TOOL_ERROR", error=str(e))
            return "Tool execution failed"
```

---

#### **4.3 API Authentication & Rate Limiting**

```python
# empire_api/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Rate limiting middleware (per user + IP)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/action")
@limiter.limit("100/minute")  # 100 requests per minute per IP
def execute_action(request: Request, action_req: ActionRequest,
                   user_id: str = Depends(verify_api_key)):
    """Execute action with auth + rate limiting"""
    # Further restrict by user API quota
    user_quota = get_user_quota(user_id)
    if user_quota.requests_today >= user_quota.limit:
        return {"error": "Daily quota exceeded"}, 429

    # Execute...
    return result
```

---

### **LAYER 5: CI/CD & SUPPLY CHAIN SECURITY**

#### **5.1 Pre-Commit Hooks**

**File**: `.git/hooks/pre-commit` (auto-installed via `/scripts/setup-hooks.sh`)

```bash
#!/bin/bash
set -e

echo "🔒 Running security checks..."

# 1. Check for secrets (hardcoded keys)
if git diff --cached | grep -iE '(api_key|password|secret|token|aws_access)'; then
    echo "❌ BLOCKED: Potential secret detected in commit"
    exit 1
fi

# 2. Check for large files (>10MB)
if git diff --cached --name-only | while read file; do
    size=$(git cat-file -s :"$file" 2>/dev/null || echo 0)
    if [ $size -gt 10485760 ]; then
        echo "❌ BLOCKED: File too large: $file ($size bytes)"
        exit 1
    fi
done; then
    exit 1
fi

# 3. Python linting
if git diff --cached --name-only | grep '\.py$'; then
    python -m pylint empire_api/ --disable=all --enable=E,F
fi

# 4. Dependency audit (locally)
pip-audit --desc

echo "✅ All checks passed"
exit 0
```

---

#### **5.2 GitHub Actions Security Gates**

**File**: `.github/workflows/security-gates.yml` (to be created)

```yaml
name: Security Gates
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for secret scanning

      # 1. Secret scanning
      - name: Detect secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
          extra_args: --only-verified

      # 2. Dependency scanning
      - uses: dependabot/dependabot-action@v14
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      # 3. Container scanning (if Dockerfile changed)
      - name: Scan Docker image
        if: contains(github.event.head_commit.modified, 'Dockerfile')
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      # 4. Code scanning (SAST)
      - name: Run CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: python

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2

      # 5. License compliance
      - name: Check licenses
        uses: fossas/fossa-action@main
        with:
          api-key: ${{ secrets.FOSSA_API_KEY }}

  approval-gate:
    runs-on: ubuntu-latest
    needs: security-scan
    if: |
      github.event_name == 'pull_request' &&
      contains(github.event.pull_request.labels.*.name, 'security:critical')
    steps:
      - name: Request approval
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.pulls.requestReviewers({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
              reviewers: ['mauricepfeifer-ctrl']  # Owner approval required
            })
```

---

### **LAYER 6: MONITORING & AUDIT LOGGING**

#### **6.1 Centralized Logging (JSON format)**

**Configuration** (`/ops/monitoring/loki-config.yml`):
```yaml
auth_enabled: false
ingester:
  chunk_idle_period: 3m
  chunk_retain_period: 1m
limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
schema_config:
  configs:
  - from: 2020-10-24
    store: boltdb-shipper
    object_store: filesystem
    schema:
      index:
        prefix: index_
        period: 24h
server:
  http_listen_port: 3100
  log_level: info
```

**Application logging** (Python):
```python
# empire_api/logging.py
import json, logging, sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utc now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

logger = logging.getLogger("empire")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Security event logging
def log_security_event(event_type: str, **kwargs):
    """Log security-relevant events for audit trail"""
    logger.warning(json.dumps({
        "event_type": event_type,
        "severity": "SECURITY",
        **kwargs
    }))
```

---

#### **6.2 Alerting Rules**

**File**: `/ops/monitoring/prometheus-rules.yml`

```yaml
groups:
- name: security_alerts
  rules:
  - alert: UnauthorizedAPIAccess
    expr: increase(api_auth_failures_total[5m]) > 5
    for: 1m
    annotations:
      severity: P2
      summary: "Multiple API auth failures ({{ $value }} in 5m)"

  - alert: HighCPUUsage
    expr: node_cpu_usage_percent > 85
    for: 5m
    annotations:
      severity: P2
      summary: "CPU > 85% - may pause agents"

  - alert: DatabaseConnectionLeak
    expr: pg_connections > 100
    for: 2m
    annotations:
      severity: P1
      summary: "PostgreSQL connection leak detected"

  - alert: HighCostBudgetExceeded
    expr: api_cost_daily_usd > 50
    for: 1m
    annotations:
      severity: P1
      summary: "Daily API cost > EUR 50"

  - alert: UnencryptedSecretAccess
    expr: increase(secrets_plaintext_read[5m]) > 0
    for: 0m
    annotations:
      severity: P1
      summary: "Plaintext secret read (possible compromise)"
```

---

## 🚨 INCIDENT RESPONSE

### **IR-1: Potential Secret Compromise**

**Trigger**: Secret detected in git history / unauthorized API access / cost spike

**Immediate (0-15 min)**:
```bash
# 1. Identify affected service
grep -r "COMPROMISED_KEY" logs/

# 2. Rotate compromised key immediately
# a. Remove old key from sops
sops .env.enc
# b. Generate new key on Moonshot dashboard
# c. Update .env.enc
# d. Redeploy

docker compose pull && docker compose up -d

# 3. Revoke old key (if API allows)
curl -X DELETE https://api.moonshot.ai/v1/keys/sk-xxxx \
  -H "Authorization: Bearer NEW_KEY"

# 4. Review audit logs for access during compromise window
grep "COMPROMISED_KEY" logs/ | jq '.timestamp' | while read ts; do
  echo "Access between $ts and $(date)"
done
```

**Follow-up (within 24h)**:
- [ ] Generate incident report (what? when? how long exposed?)
- [ ] Review access logs for data exfiltration
- [ ] Count API calls during compromise (estimate attacker actions)
- [ ] Update secret rotation policy if gap identified
- [ ] Notify affected customers (if data accessed)

---

### **IR-2: Unauthorized Agent Execution (Prompt Injection)**

**Trigger**: Agent executed dangerous command / exfiltrated data / wrote to forbidden path

**Immediate (0-15 min)**:
```bash
# 1. Pause all agents
redis-cli flushall  # Clear task queue
curl -X POST http://localhost:3333/api/pause-agents

# 2. Analyze executor logs
journalctl -u empire-api -S "15 minutes ago" | grep "TOOL_EXECUTED"
docker logs empire-api | grep "execute_tool" | tail -50

# 3. Identify injection vector
# a. Was it user input? Disable that user's API key
# b. Was it malicious dependency? Scan all commands in git diff
# c. Was it LLM output? Review LLM call history

git log --oneline -20 | xargs -I {} \
  git show {} | grep -E "(execute|tool|system|shell)"

# 4. Kill compromised agent process (if running)
docker kill $(docker ps | grep brain-system | awk '{print $1}')

# 5. Restore from clean backup
./ops/backup/restore-from-backup.sh --timestamp "2h ago"
```

**Follow-up (within 24h)**:
- [ ] Post-mortem: What was the injection point?
- [ ] Update prompt templates to be more defensive
- [ ] Add input validation for that command type
- [ ] Run chaos test: Try to break it again

---

### **IR-3: Database Breach / Data Loss**

**Trigger**: Unauthorized access to PostgreSQL / Ransomware / Disk failure

**Immediate (0-15 min)**:
```bash
# 1. Disconnect from network (isolate to prevent lateral movement)
sudo ifconfig en0 down  # macOS
# or
sudo ip link set eth0 down  # Linux

# 2. Take disk image for forensics
dd if=/dev/sda of=/mnt/usb/forensics-image.dd bs=4M

# 3. Power down (don't force kill, risk corruption)
sudo shutdown -h now

# 4. Power on from external USB (clean OS)
# Boot Ubuntu Live USB, mount original disk read-only
# Analyze logs + memory dumps for attacker activity

# 5. Restore from backup (with point-in-time recovery if available)
```

**Follow-up (within 48h)**:
- [ ] Forensic analysis (timeline of events)
- [ ] Root cause (were backups encrypted? Accessible?)
- [ ] Data loss assessment (what was lost? customer impact?)
- [ ] Notify customers if PII exposed
- [ ] Harden backup strategy (offline backup vault?)

---

## ✅ SECURITY CHECKLIST (MVP)

- [ ] Firewall configured (UFW deny-all inbound)
- [ ] VPN setup (Tailscale), all services behind it
- [ ] TLS/mTLS enabled (Traefik reverse proxy)
- [ ] Secrets encrypted (sops + age)
- [ ] Secrets rotated (API keys every 90 days)
- [ ] Containers hardened (no root, seccomp, cap drop)
- [ ] Images scanned (trivy, no HIGH/CRITICAL vulns)
- [ ] Pre-commit hooks active (no secrets, no large files)
- [ ] CI/CD gates enabled (sec scan, license check, approval for critical)
- [ ] Audit logging active (JSON format, all actions logged)
- [ ] Rate limiting enabled (API endpoints, Redis cli)
- [ ] Backup tested (restore from backup works)
- [ ] Incident response plan documented (this file + runbooks)
- [ ] Security policy signed (Maurice approval below)
- [ ] Compliance audit done (GDPR, DIN, ISO - baseline)

---

## 📋 COMPLIANCE & POLICY

### **GDPR Readiness**
- [ ] Data inventory (what personal data do we store?)
- [ ] Data processing agreements (with Moonshot, OpenAI, etc.)
- [ ] Right to erasure (can we delete user data on request?)
- [ ] Data breach notification process (<72 hours)
- [ ] Privacy policy published (if customers access system)

### **DIN (German Data Protection)**
- Same as GDPR + local requirements
- Audit trail for all data access
- Encryption at rest + in transit

### **ISO 27001 (Information Security)**
- Risk assessment (done above)
- Control framework (this document)
- Regular audits (quarterly)
- Incident response plan (done above)

---

## 🚀 DEPLOYMENT SECURITY CHECKLIST

**Before going live with ANY service**:
- [ ] All secrets moved to vault (no .env in git)
- [ ] TLS certificate generated (self-signed or Let's Encrypt)
- [ ] Firewall rules applied (deny-all default)
- [ ] Rate limits configured (API, Redis, SSH)
- [ ] Audit logging enabled (sent to Loki/aggregation)
- [ ] Backups tested (restore works)
- [ ] Monitoring alerts configured (P1/P2/P3 routing)
- [ ] Security gates passing (no vulnerabilities)
- [ ] Incident response plan reviewed (team trained)
- [ ] External audit requested (if handling customer data)

---

## 📞 SECURITY CONTACTS

| Role | Contact | Escalation |
|------|---------|-----------|
| **Chief Security Officer** | CLAUDE | 24/7 (automated alerts) |
| **CEO** | Maurice (mauricepfeifer@...) | P1 incidents |
| **On-Call Ops** | TBD | P2 incidents |

---

**END OF SECURITY.md**

---

## ✍️ APPROVAL & SIGN-OFF

- **Security Policy Approved By**: _CLAUDE_ (2026-02-10)
- **Maurice Review**: _PENDING_ (target: 2026-02-10)
- **Last Audit**: 2026-02-10
- **Next Audit**: 2026-05-10 (quarterly)

