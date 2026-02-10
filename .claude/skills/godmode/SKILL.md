---
name: godmode
description: >
  Secure-by-default autonomous builder for an open-source 24/7 AI empire.
  Use when planning/architecting/implementing always-on agent ecosystems, repo automation,
  CI/CD hardening, threat modeling, sandboxing, secrets management, monitoring, backups,
  and “autonomy with guardrails” execution systems. Keywords: 24/7, autonomous, agents,
  orchestration, open source, security, hardening, threat model, CI, GitHub Actions,
  least privilege, sandbox, docker, podman, reverse proxy, VPN, Tailscale, WireGuard,
  secrets, sops, age, Vault, monitoring, alerts, backups, incident response, runbooks.
---

# GODMODE Skill — Secure Autonomous Empire Builder (Open Source, 24/7)

## Purpose
This skill turns a repository into a **secure, always-on, open-source agent ecosystem** that can run 24/7 with **maximum operational safety**. It is designed to:
- Clarify founder **vision → strategy → roadmap**
- Build **modular architecture** for autonomous systems
- Implement **security-by-design** hardening for long-running operation
- Add **guardrails** so autonomy does not become chaos
- Produce **commit-ready repo artifacts** (docs, configs, workflows, runbooks)

This skill is **defensive** and **operations-first**. It explicitly avoids providing instructions that enable hacking, intrusion, or exploitation.

---

## When to Use
Use this skill when the user asks for:
- “Build my AI empire / autonomous system 24/7”
- “Open source, self-hosted, secure, production-grade”
- “Set up agents that triage issues/PRs and auto-merge safely”
- “Max security against hackers / external threats / zero trust”
- “Create architecture + workflows + monitoring + backups + runbooks”
- “Turn big vision into executable plan and ship”

---

## Core Principles (Non-Negotiable)
1) **Security before features**  
   If uncertain, block and propose a safer alternative.
2) **No offensive instructions**  
   Do not provide exploit steps, intrusion guidance, or bypass methods. Provide only defensive best practices, configuration guidance, and hardening.
3) **Least privilege everywhere**  
   Minimal access, minimal services, minimal ports. Default deny.
4) **Autonomy with guardrails**  
   Agents can act, but only within sandboxed scopes and with explicit gates.
5) **Reproducible & auditable**  
   Everything as code/config. Produce logs/audit trails for agent actions.
6) **Operational excellence**  
   Observability, backup/restore testing, incident response runbooks are mandatory.

---

## Required Workflow (How to Execute This Skill)
Always follow this sequence (V1 first, then iterate):

### Step 0 — Establish context quickly (no stalling)
- Infer environment (macOS/Linux, Docker/Podman, repo stack).
- If critical unknowns exist, ask **max 5 short questions** at the end.
- Otherwise proceed with safe defaults and mark assumptions.

### Step 1 — Vision Extraction → Strategy Compression
Produce `docs/VISION.md` with:
- 1-sentence mission
- 3-year vision (≤5 bullets)
- 12-month goals
- 90-day bets (≤3)
- North Star Metric + 5 KPIs
- Target user + “why now”
- Anti-goals (what we will not do)

### Step 2 — Architecture (Modular & Safe)
Produce `docs/ARCHITECTURE.md` with:
- Components:
  - Orchestrator
  - Agent roles (research/content/dev/ops/qa/security/growth)
  - Memory/data layer (local, versioned, auditable)
  - Interfaces (CLI/WebUI/Telegram)
  - Observability (logs/metrics/alerts)
- Threat boundaries & trust zones
- Mermaid diagrams (system + data flow)

### Step 3 — Threat Model (Defensive)
Produce `docs/SECURITY.md` with:
- Attacker types: scanners, credential stuffing, supply chain, misconfig, insider, prompt-injection
- Assets: secrets, data, automation credentials, CI tokens, backups
- Attack surfaces: exposed ports, WebUIs, SSH, actions permissions, dependencies, agent tools
- Controls & mitigations mapped to threats

### Step 4 — Hardening Implementation (Concrete)
Create commit-ready configs for:
- Network perimeter: VPN-first; no public exposure by default
- Reverse proxy (Caddy/Traefik) with TLS and optional mTLS
- Firewall guidance (deny-all inbound)
- Secrets handling: no secrets in repo; sops+age or OS keychain; rotate policy
- Container hardening:
  - run as non-root
  - read-only FS where possible
  - drop Linux capabilities
  - `no-new-privileges`
  - minimal networks
- Supply chain:
  - pinned versions + lockfiles
  - dependabot/renovate
  - minimal GitHub Actions permissions
- CI gates:
  - lint + tests + security scans + policy checks
  - automerge only on low-risk label + green checks

### Step 5 — Autonomy Guardrails (Prevent Chaos)
Define:
- Tool sandboxing: allowlist commands and paths, restrict shell
- Dry-run default for destructive tasks
- Rate limits, retries/backoff, dead-letter mechanism
- Idempotent task execution
- Manual gate for high-risk actions (owner ping)

### Step 6 — Observability + Backups + Runbooks
Create:
- logging and metrics setup (choose simple defaults)
- alert rules for suspicious behavior and service health
- 3-2-1 backup strategy
- restore test script
- incident response runbooks (what to do when X happens)

---

## Output Contract (Mandatory Format)
Every response using this skill must use:

A) **Deliverables** (copy/paste: files, commands, configs)  
B) **Assumptions** (short)  
C) **Security Analysis** (top 5 risks + mitigations)  
D) **Next Steps** (exact steps in order)  
E) **Rollback Plan** (how to revert safely)

---

## Repo Deliverables Checklist (Default)
Unless the user specifies otherwise, generate:
1) `docs/VISION.md`
2) `docs/ARCHITECTURE.md` (Mermaid)
3) `docs/SECURITY.md` (Threat model + mitigations + policies)
4) `ops/docker-compose.yml` (or Podman)
5) `ops/proxy/` (Caddy or Traefik config)
6) `.github/workflows/ci.yml`
7) `.github/workflows/auto-triage.yml`
8) `ops/backup/backup.sh` + `ops/backup/restore-test.sh`
9) `ops/monitoring/` (simple stack + instructions)
10) `ops/runbooks/incident-response.md`

---

## Label & Risk Gate Policy (for PR Automation)
Risk labels:
- `risk:low` docs/tests/comments, tiny refactor, no behavior change
- `risk:med` limited behavior change w/ tests
- `risk:high` infra/deploy/auth/security/secrets/permissions, broad refactor

Automerge only if:
- `risk:low`
- CI green
- no `.github/workflows` or infra touched
- no permissions expanded
- no new network exposure

Escalate to owner only if:
- `risk:high` OR release/deploy impact OR CI flake near merge

Owner ping format (single message):
- What changed
- Why it matters
- Risk (1–10)
- Decision needed
- Rollback plan

---

## Safety Boundaries (Must Follow)
### Allowed
- Hardening steps, configuration best practices
- Defensive scanning (secret scanning, dependency scanning)
- Threat modeling, least privilege, firewall/VPN guidance
- Incident response procedures
- Secure coding patterns

### Not Allowed
- Exploit/intrusion instructions
- Bypassing authentication, malware, phishing, credential theft
- Step-by-step hacking playbooks

If user requests offensive steps:
- Refuse those parts, then provide defensive alternatives.

---

## Examples

### Example 1 — “Make my repo 24/7 autonomous and secure”
**Input:**  
“Build my open-source AI empire that runs 24/7 and prevent hackers.”

**Expected Output (abbrev):**
- Provide `docs/VISION.md` template with inferred mission
- Create `docs/SECURITY.md` with threat model & mitigations
- Add `.github/workflows/ci.yml` with lint/tests/dep scan
- Provide `docker-compose.yml` with non-root containers, isolated networks
- Provide backup scripts and runbooks
- Escalation/merge gates

### Example 2 — “Auto-triage issues and PRs, ping me only 1%”
**Input:**  
“24/7 PR checks, auto labels, only ask me at the end.”

**Expected Output:**
- Risk labeling policy
- `auto-triage.yml` workflow
- Branch protection recommendations
- PR template with security checklist
- Owner escalation rules

### Example 3 — “We need VPN-first and no public exposure”
**Input:**  
“Everything must be private and accessible only via VPN.”

**Expected Output:**
- VPN-first architecture
- reverse proxy bound to local/VPN interface only
- firewall deny-all inbound except VPN
- zero public DNS requirement
- remote access SOP

---

## Minimal Questions (Ask only if truly necessary)
1) OS + host (macOS/Linux) and whether Docker or Podman
2) Which services must run 24/7 (n8n, OpenWebUI, Ollama, etc.)
3) Whether anything must be public-facing (default: no)
4) Repo stack (Node/Python/Go)
5) Preferred VPN (Tailscale/WireGuard) or none

If unknown, proceed with safe defaults and mark assumptions.

---

## Quality Bar
- Ship V1 fast, but never compromise core security gates.
- Prefer simple, proven components over complex ones.
- Every automation must have logs, limits, and rollback.