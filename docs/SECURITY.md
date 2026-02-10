# AI Empire Security & Threat Model

**Version:** 1.0
**Last Updated:** 2026-02-10
**Classification:** P1 (Restricted)

---

## Executive Summary

AIEmpire-Core is a **highly valuable, high-risk autonomous system** that requires:
1. **Zero public exposure** (VPN-first architecture)
2. **Insider threat protection** (code review for all agent outputs)
3. **Supply chain hardening** (pinned dependencies, minimal CI permissions)
4. **Data privacy enforced** (P3 data never leaves Mac)
5. **Incident response readiness** (monitoring, backups, runbooks)

**Target:** 3 years, zero security breaches; 99.9% uptime; full audit trail.

---

## Asset Inventory

### High-Value Assets
| Asset | Value | Location | Risk |
|-------|-------|----------|------|
| **Claude API Key** | EUR 30K/year | macOS Keychain | **CRITICAL** |
| **Kimi API Key (Budget $12)** | EUR 10K/year | macOS Keychain | **CRITICAL** |
| **GitHub Token (repo admin)** | Unlimited merge access | macOS Keychain | **CRITICAL** |
| **Gumroad API Key** | EUR 100K+ annual sales | macOS Keychain | **CRITICAL** |
| **PostgreSQL Data** | Legal docs, CRM, financials | Localhost DB | **HIGH** |
| **Private Vault (~/.private-vault/)** | P3 restricted data, trade secrets | Local filesystem | **CRITICAL** |
| **Redis Queue** | Active tasks, state | Localhost | **HIGH** |
| **Ollama Models** | 95% of operations | Localhost | **MEDIUM** |
| **X/Twitter Account** | 500+ leads/month | OAuth token | **HIGH** |
| **Backups (encrypted)** | Full system state | Local disk + cloud | **CRITICAL** |

---

## Threat Model

### Attacker Personas

#### 1. External Scanners & Bots
**Goal:** Find exploitable ports, services, or API endpoints.
**Tools:** Shodan, masscan, automated vulnerability scanners.
**Tactics:** Port scanning, brute force, default credentials.

**Risk:** **MEDIUM** (mitigated by VPN-first, no public exposure)
**Current Status:** No public services exposed.

#### 2. Credential Stuffing / Supply Chain Attackers
**Goal:** Steal API keys, GitHub tokens, database passwords.
**Tactics:** Leak databases, GitHub public repos, env files, npm typosquatting.
**Tools:** Leaked credential databases, dependency injection.

**Risk:** **HIGH** (macOS Keychain limits scope, but secrets still valuable)
**Critical Assets:** Claude API, Kimi API, GitHub token, Gumroad API.

#### 3. Cloud API Provider Compromise
**Goal:** Access all P0/P1 data sent to Kimi/Claude.
**Tactics:** Exploit cloud provider, insider access, nation-state TLA.
**Tools:** Backdoored models, log access.

**Risk:** **MEDIUM** (only P0/P1 data sent; redacted)
**Mitigation:** Never send P2 or P3 data to cloud; audit Kimi/Claude privacy policies quarterly.

#### 4. GitHub Actions Vulnerabilities
**Goal:** Extract secrets, run malicious code on Mac.
**Tactics:** Exploit untrusted workflows, inject malicious PRs, approve without review.
**Tools:** Compromised GitHub Actions, malicious third-party actions.

**Risk:** **HIGH** (directly executes code on Mac)
**Mitigation:** No untrusted Actions; code review before merge; minimal permissions.

#### 5. Local Malware / Insider Threat
**Goal:** Exfiltrate all data, delete backups, disable monitoring.
**Tactics:** Infected npm package, malicious Python dependency, bad shell alias.
**Tactics:** Social engineering Maurice.

**Risk:** **CRITICAL** (local access = full compromise)
**Mitigation:** Private Vault encryption, backup verification, code review for all dependencies.

#### 6. Prompt Injection / Agent Manipulation
**Goal:** Make agents exfiltrate data or execute unauthorized commands.
**Tactics:** Craft prompts that "jailbreak" agents, bypass guardrails.
**Tools:** LLM jailbreak prompts, malicious task inputs.

**Risk:** **HIGH** (agents execute potentially dangerous operations)
**Mitigation:** Dry-run default, manual gate for destructive actions, allowlist sandbox.

#### 7. Ransomware / Data Destruction
**Goal:** Encrypt backups, delete GitHub repos, corrupt PostgreSQL.
**Tactics:** Malicious code in dependencies, unpatched OS, weak backup security.

**Risk:** **CRITICAL** (destroys EUR 100M+ business)
**Mitigation:** 3-2-1 backups, immutable backups (versioned), offline backup copy.

#### 8. Denial of Service (DoS)
**Goal:** Crash services, cause SLA breach, financial loss.
**Tactics:** Overwhelming API calls, malicious scheduled tasks, infinite loops in agents.

**Risk:** **MEDIUM** (high business impact, but detectable)
**Mitigation:** Rate limits, Resource Guard auto-throttling, timeout guards.

---

## Attack Surface

### Surface 1: Local Mac Filesystem
**Exposed Components:**
- `~/.zshrc` / `~/.bash_profile` (shell config, aliases, env vars)
- `~/.aws/` (if AWS CLI installed)
- `~/.ssh/` (private keys if no passphrase)
- `.env` files in projects (if not gitignored)
- Browser cache/cookies (GitHub, Gumroad, X login)
- `/tmp/` (world-writable, plaintext)

**Threats:** Credential theft, SSH key hijacking, session hijacking.

**Mitigations:**
- [ ] Keep `~/.zshrc` clean; no secrets in shell config
- [ ] Use macOS Keychain for all API keys, never env vars
- [ ] SSH keys must have passphrase
- [ ] `.env` in `.gitignore`; use `cp .env.example .env`
- [ ] Browser cookie isolation (separate browser profile for each service)
- [ ] `/tmp/` scripts: mark as executable-only, not readable

### Surface 2: Network Services (VPN-only)
**Exposed Components:**
- OpenClaw (18789)
- Atomic Reactor (8888)
- CRM (3500)
- PostgreSQL query API (5432)
- Redis (6379)

**Threats:** Unauthorized access, query injection, data exfiltration.

**Mitigations:**
- [ ] VPN-only access (Tailscale mesh), no public DNS
- [ ] Password-protected dashboards (OpenClaw, CRM)
- [ ] PostgreSQL/Redis: localhost-only, no remote connections
- [ ] Caddy reverse proxy with TLS 1.3 mandatory
- [ ] Rate limits on all endpoints
- [ ] Input validation on all APIs

### Surface 3: GitHub & CI/CD
**Exposed Components:**
- `.github/workflows/` (runs arbitrary code on Mac)
- GitHub Actions secrets (Claude API, Kimi API, etc.)
- GitHub token (repo admin access)
- Pull requests from external contributors

**Threats:** Code injection, secret extraction, unauthorized merge.

**Mitigations:**
- [ ] No untrusted GitHub Actions; vendored scripts only
- [ ] Minimal CI permissions: read repo, write to PRs only (no admin)
- [ ] Secrets encrypted at rest (GitHub Secrets Manager)
- [ ] Code review required for all PRs, especially `.github/workflows/`
- [ ] Branch protection: require CI green + review + no auto-merge on sensitive branches
- [ ] Audit GitHub access logs monthly

### Surface 4: Cloud LLM APIs (Kimi, Claude)
**Exposed Components:**
- API keys sent to api.moonshot.ai and api.anthropic.com
- Request/response data logged by cloud providers
- Model weights/fine-tuning data

**Threats:** Data logging, insider access, model theft, request correlation.

**Mitigations:**
- [ ] P0/P1 data only (public, non-sensitive)
- [ ] Redact secrets before sending (API keys, credentials, emails)
- [ ] Redact P2/P3 entirely; use Ollama instead
- [ ] Request hashing to prevent exact matching by provider
- [ ] Monthly privacy policy audit (Kimi & Claude terms)
- [ ] Estimate data flow: <5% of total data leaves Mac

### Surface 5: Dependencies & Dependency Graph
**Exposed Components:**
- npm packages (CRM, monitoring)
- Python packages (Ollama, LLM APIs, FastAPI)
- GitHub Actions (marketplace actions)

**Threats:** Typosquatting, supply chain poisoning, hidden backdoors, zero-day CVEs.

**Mitigations:**
- [ ] Pinned versions (no `^` or `~`, use exact)
- [ ] Lockfiles committed to repo (package-lock.json, requirements.txt)
- [ ] Dependabot enabled, automatic PRs for security patches
- [ ] npm audit & pip audit in CI, fail on vulnerabilities
- [ ] No `postinstall` scripts unless from trusted sources
- [ ] Review new package additions carefully
- [ ] Use `npm ci` (not `npm install`) in CI to enforce lockfile

### Surface 6: X/Twitter, Gumroad, CRM Integrations
**Exposed Components:**
- OAuth tokens (X, Gumroad)
- Lead data (emails, names, companies)
- Financial data (revenue, transactions)

**Threats:** Account takeover, lead harvesting, financial fraud.

**Mitigations:**
- [ ] OAuth tokens in macOS Keychain only
- [ ] Disable API access if not in use
- [ ] Audit OAuth scopes: minimal permissions
- [ ] CRM data encrypted at rest (PostgreSQL cell-level encryption future)
- [ ] Monthly access logs audit (X, Gumroad)
- [ ] Disable old/unused integrations

### Surface 7: Backups
**Exposed Components:**
- Encrypted backups (local disk)
- Cloud backup copy (if using B2, S3, etc.)
- Restore test scripts

**Threats:** Ransomware, backup corruption, lost restore capability.

**Mitigations:**
- [ ] **3-2-1 strategy:** 3 copies (original + 2 backups), 2 media (disk + cloud), 1 offsite
- [ ] **Encryption at rest:** AES-256 (using `openssl enc` or `age`)
- [ ] **Immutable backups:** Versioned, write-once (S3 Object Lock if using AWS)
- [ ] **Offline backup copy:** One backup on external USB drive, stored offline
- [ ] **Test restores monthly:** Verify backups not corrupted
- [ ] **Backup monitoring:** Alert if backup fails 2+ times

---

## Security Controls & Mitigations

### Control 1: Defense in Depth (Layered Security)
| Layer | Control | Status |
|-------|---------|--------|
| **Network** | VPN-first (Tailscale), no public exposure | ✅ PLANNED |
| **Application** | Input validation, rate limiting, error handling | ✅ PLANNED |
| **Data** | Encryption at rest (P3), encrypted backups | ✅ PLANNED |
| **Access** | Keychain (macOS), no env vars, minimal CI permissions | ✅ IN PROGRESS |
| **Monitoring** | Logs, metrics, alerts, incident response | ✅ PLANNED |

### Control 2: Secrets Management
**Policy:**
- [ ] No secrets in code, `.env` files, or shell config
- [ ] All API keys → macOS Keychain
- [ ] All passwords → macOS Keychain (or 1Password if team expands)
- [ ] Rotate secrets quarterly (API keys, GitHub tokens after 90 days)
- [ ] Audit Keychain access monthly

**Implementation:**
```bash
# Store secret
security add-generic-password -a "claude-api-key" -s "AIEmpire" -w "sk-..."

# Retrieve secret (in Python scripts)
import subprocess
def get_secret(account, service):
    cmd = f'security find-generic-password -a "{account}" -s "{service}" -w'
    return subprocess.check_output(cmd, shell=True).decode().strip()

# In scripts: Never echo, never log, never debug print
CLAUDE_API_KEY = get_secret("claude-api-key", "AIEmpire")
```

### Control 3: Network Perimeter
**Policy:**
- [ ] All services default to localhost (127.0.0.1)
- [ ] VPN-only access via Tailscale (100.x.x.x)
- [ ] macOS firewall enabled, deny-all inbound except VPN
- [ ] No public DNS records for internal services
- [ ] Caddy reverse proxy: TLS 1.3 mandatory

**Implementation:**
```bash
# Firewall: deny all, allow Tailscale only
sudo pfctl -e
sudo pfctl -f /etc/pf.conf  # Custom rules

# Verify bindings (no public exposure)
lsof -i -P -n | grep LISTEN
# Should show: 127.0.0.1:6379, 127.0.0.1:5432, 127.0.0.1:11434, etc.
```

### Control 4: Container Hardening (Future Docker/Podman)
**Policy:**
- [ ] Run as non-root (UID 1000)
- [ ] Read-only root filesystem (where possible)
- [ ] Drop all Linux capabilities except required
- [ ] `no-new-privileges` flag
- [ ] Minimal base images (Alpine, distroless)
- [ ] Resource limits (CPU, memory)

**Example Dockerfile Fragment:**
```dockerfile
FROM python:3.11-slim

RUN groupadd -r aiempire && useradd -r -g aiempire aiempire

COPY --chown=aiempire:aiempire . /app

USER aiempire

RUN chmod 555 /app  # Read-only

CMD ["python", "-u", "main.py"]
```

### Control 5: Supply Chain Security
**Policy:**
- [ ] Pinned dependency versions (no `^` or `~`)
- [ ] Lockfiles committed (package-lock.json, requirements.txt)
- [ ] Dependabot enabled, automatic patches
- [ ] npm audit + pip audit in CI, fail on vulnerabilities
- [ ] No `postinstall` scripts from untrusted packages
- [ ] Code review for new dependencies

**Implementation:**
```bash
# CI check
npm audit --audit-level=moderate && exit 1
pip check && pip-audit
```

### Control 6: Code Review & Approval Gates
**Policy:**
- [ ] All PRs require 1x code review
- [ ] `.github/workflows/` require 2x review
- [ ] `ops/` changes require 2x review
- [ ] No auto-merge on sensitive branches (default, develop, main)
- [ ] Risk labels mandatory: `risk:low`, `risk:med`, `risk:high`
- [ ] High-risk PRs require owner approval

**Branch Protection (GitHub):**
```yaml
# main branch
- Require pull request reviews: 1
- Require status checks to pass (before merge)
- Require branches to be up to date
- Require code review before merging
- Require approval of reviews
- Auto-delete head branches
```

### Control 7: Audit Logging & Monitoring
**Policy:**
- [ ] All API calls logged (URI, params, response code, latency)
- [ ] All database queries logged (slow query log, query plans)
- [ ] All agent actions logged (task ID, action, output, cost)
- [ ] Security events logged (auth failures, permission denials, suspicious commands)
- [ ] Logs retained 90 days, searchable

**Implementation:**
```python
import json
import time

def log_api_call(method, uri, status, latency, user):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "method": method,
        "uri": uri,
        "status": status,
        "latency_ms": latency,
        "user": user,
    }
    with open("/var/log/aiempire-api.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

### Control 8: Incident Response
**Policy:**
- [ ] Critical incidents: <5 minute response, <15 minute mitigation
- [ ] High incidents: <30 minute response, <1 hour mitigation
- [ ] Medium incidents: <2 hour response, <4 hour mitigation
- [ ] All incidents logged with impact, root cause, remediation
- [ ] Runbooks for common scenarios (data breach, service crash, credential leak)

**Runbook Template:**
```markdown
# Incident: [Name]
Severity: [CRITICAL/HIGH/MEDIUM/LOW]
Time To Detect: [X minutes]
Time To Respond: [Y minutes]
Impact: [Description]

## Detection
[How we know this happened]

## Containment
[Immediate actions to stop damage]
1. [Action]
2. [Action]

## Remediation
[Fix the root cause]
1. [Action]
2. [Action]

## Recovery
[Restore normal operations]
1. [Action]
2. [Action]

## Post-Incident
[Lessons learned, prevention]
- [Improvement]
```

---

## Risk Matrix

| Threat | Probability | Impact | Risk | Mitigation | Priority |
|--------|-------------|--------|------|------------|----------|
| **API Key Leak** | Medium | CRITICAL (EUR 30K) | **HIGH** | Keychain, rotate Q | P0 |
| **Cloud API Breach** | Low | HIGH (P0/P1 data) | MEDIUM | Redact, audit | P1 |
| **GitHub Actions Hijack** | Medium | CRITICAL (code exec) | **HIGH** | Code review, minimal CI | P0 |
| **Ransomware/Backups Deleted** | Low | CRITICAL (data loss) | **HIGH** | 3-2-1, offline copy | P0 |
| **Prompt Injection** | Medium | HIGH (unauthorized actions) | **HIGH** | Dry-run, guardrails | P1 |
| **Supply Chain (npm/pip)** | Medium | MEDIUM (backdoor) | **MEDIUM** | Pinned versions, audit | P1 |
| **Insider Threat** | Low | CRITICAL (full compromise) | **HIGH** | Keychain, code review | P0 |
| **DDoS / Rate Limit** | Low | MEDIUM (outage) | LOW | Rate limits, throttling | P2 |
| **Phishing (Maurice)** | Medium | HIGH (credential theft) | **HIGH** | MFA, security training | P1 |
| **Typosquatting / Dependency** | Medium | MEDIUM | **MEDIUM** | Audit, npm audit | P1 |

---

## Security Checklist (Pre-Production)

- [ ] **Secrets:**
  - [ ] All API keys in macOS Keychain
  - [ ] No secrets in `.env`, code, shell config
  - [ ] Rotation schedule (Q on calendar)
  - [ ] No plaintext API keys in any logs

- [ ] **Network:**
  - [ ] All services localhost-only
  - [ ] VPN (Tailscale) configured
  - [ ] macOS firewall enabled
  - [ ] Caddy reverse proxy TLS 1.3
  - [ ] Port scan: verify no public exposure

- [ ] **Code:**
  - [ ] Dependencies pinned (no `^`, `~`)
  - [ ] Lockfiles committed
  - [ ] npm audit / pip audit green
  - [ ] Code review process established
  - [ ] Branch protection: main + develop

- [ ] **Monitoring:**
  - [ ] Logging configured (API, DB, agents)
  - [ ] Alert rules set (failed auth, high CPU, low disk)
  - [ ] Backup automation running
  - [ ] Restore test passed

- [ ] **Documentation:**
  - [ ] Runbooks written (5 common incidents)
  - [ ] Recovery procedures tested
  - [ ] Escalation path clear (Maurice contact info)
  - [ ] Security policy reviewed

---

## Compliance & Privacy

### GDPR (EU General Data Protection Regulation)
- **Data Processing:** CRM lead data (emails, names, companies)
- **Legal Basis:** Legitimate interest (marketing to contractors)
- **Data Subjects:** BMA contractors, potential customers
- **Rights:** Access, rectification, erasure on request
- **Retention:** 3 years unless actively engaged

**Actions:**
- [ ] Privacy notice in Gumroad products
- [ ] Unsubscribe link in all emails
- [ ] Data deletion process documented
- [ ] DPA (if using cloud processors like Kimi)

### German Data Protection (Datenschutz)
- **Betriebsrat:** Not applicable (solo founder)
- **Datenverarbeitung:** Only Maurice (no employees)
- **Responsible:** Maurice Pfeifer

### BMA Legal (Brandmeldeanlagen)
- **Classification:** Trade secret (BMA knowledge)
- **P3 Data:** Never to cloud, never exported
- **Liability:** EUR 30K-140K in Rechtsstreit (2026 settlement pending)

---

## Security Roadmap

### Phase 1: Immediate (Feb 2026)
- [ ] Keychain setup complete
- [ ] VPN (Tailscale) configured
- [ ] GitHub actions: code review process active
- [ ] Backup automation live
- [ ] Runbooks (3 critical scenarios)

### Phase 2: Short-term (Q1 2026)
- [ ] Monitoring & alerts active
- [ ] Dependency audit tooling (Dependabot, Renovate)
- [ ] Restore test monthly (calendar alarm)
- [ ] Security review (quarterly)

### Phase 3: Medium-term (Q2 2026)
- [ ] Container hardening (Docker/Podman)
- [ ] Network segmentation (advanced Tailscale rules)
- [ ] mTLS for service-to-service auth
- [ ] Encryption at rest (PostgreSQL, Redis)

### Phase 4: Long-term (Q3-Q4 2026)
- [ ] SIEM (centralized log analysis)
- [ ] Threat intelligence feeds
- [ ] Red team exercise (simulate breach)
- [ ] Security certification (ISO 27001 future)

---

## Emergency Response

**CRITICAL Security Incident (API Key Leak, Data Breach):**

1. **Immediate (0-5 min):**
   - [ ] Stop all operations (kill OpenClaw, Atomic Reactor)
   - [ ] Revoke compromised API key
   - [ ] Disconnect VPN, shut down network access

2. **Short-term (5-30 min):**
   - [ ] Assess damage: what data/keys exposed?
   - [ ] Notify relevant services (GitHub, Gumroad, Kimi, Claude)
   - [ ] Initiate incident report

3. **Medium-term (30 min - 2 hours):**
   - [ ] Rotate all secrets (API keys, GitHub token, OAuth)
   - [ ] Review logs for attacker activity
   - [ ] Restore from clean backup if necessary

4. **Post-Incident (within 24 hours):**
   - [ ] Root cause analysis
   - [ ] Remediation (patch, config change)
   - [ ] Postmortem document
   - [ ] Communication to stakeholders (if applicable)

**Escalation:** Maurice Pfeifer (phone + email, 24/7)

---

**Last Updated:** 2026-02-10
**Review Cadence:** Quarterly or after incident
**Owner:** Maurice Pfeifer
**Status:** IN IMPLEMENTATION
