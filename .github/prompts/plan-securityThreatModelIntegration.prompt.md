## Plan: Security & Threat Model Integration

**TL;DR**  
Das Ziel ist, das AI Empire Security & Threat Model vollständig in die Codebasis und Betriebsprozesse zu integrieren. Dies umfasst Netzwerk-, Container-, Secrets-, Application-, CI/CD-, Monitoring- und Incident Response-Hardening. Die Umsetzung erfolgt schrittweise, orientiert an den im Security.md definierten Controls und Checklisten. Alle Maßnahmen werden so gestaltet, dass sie "secure-by-default" sind und die Prinzipien Least Privilege, Defense in Depth und Observability First einhalten.

**Steps**

1. **Netzwerk & Perimeter**
   - UFW/iptables aktivieren und konfigurieren ([bootstrap_agent_swarm.sh](bootstrap_agent_swarm.sh), [atomic-reactor/docker-compose.yaml](atomic-reactor/docker-compose.yaml))
   - Tailscale/WireGuard Deployment ([ops/traefik/docker-compose.override.yml](ops/traefik/docker-compose.override.yml))
   - Traefik Reverse Proxy mit mTLS, Rate Limiting und Logging ([ops/traefik/docker-compose.override.yml](ops/traefik/docker-compose.override.yml))

2. **Secrets Management**
   - Migration von `.env` zu sops/age ([requirements.txt](requirements.txt), [scripts/rotate_secrets.py](scripts/rotate_secrets.py))
   - CI/CD Integration für Secrets-Decryption ([.github/workflows/deploy.yml](.github/workflows/deploy.yml))
   - Rotation Policies und Alerts ([scripts/rotate_secrets.py](scripts/rotate_secrets.py), GitHub Actions Cron)

3. **Container & OS Hardening**
   - Rootless Docker/Podman Setup ([atomic-reactor/docker-compose.yaml](atomic-reactor/docker-compose.yaml))
   - Hardened Dockerfile mit User, Cap-Drop, Read-Only, Healthcheck ([atomic-reactor/tasks/](atomic-reactor/tasks/))
   - Security Scanning (Trivy, Syft, Cosign) ([scripts/](scripts/))
   - Seccomp/AppArmor Profile ([ops/security/seccomp-profile.json](ops/security/seccomp-profile.json))

4. **Application Security**
   - Input Validation gegen Prompt Injection ([empire_api/security.py](empire_api/security.py))
   - Agent Sandboxing mit Allowlist und Capability Dropping ([agents/base_agent.py](agents/base_agent.py))
   - API Auth & Rate Limiting ([empire_api/security.py](empire_api/security.py))

5. **CI/CD & Supply Chain Security**
   - Pre-Commit Hooks für Secrets, Linting, Audit ([scripts/setup-hooks.sh](scripts/setup-hooks.sh), `.git/hooks/pre-commit`)
   - GitHub Actions Security Gates ([.github/workflows/security-gates.yml](.github/workflows/security-gates.yml))

6. **Monitoring & Audit Logging**
   - Zentralisiertes Logging (JSON) ([empire_api/logging.py](empire_api/logging.py), [ops/monitoring/loki-config.yml](ops/monitoring/loki-config.yml))
   - Prometheus Alerting ([ops/monitoring/prometheus-rules.yml](ops/monitoring/prometheus-rules.yml))

7. **Incident Response**
   - Automatisierte Scripts für Key Rotation, Container Stop, UFW Block ([scripts/rotate_secrets.py](scripts/rotate_secrets.py), [bootstrap_agent_swarm.sh](bootstrap_agent_swarm.sh))
   - Dokumentation und Checklisten für IR ([SECURITY.md](SECURITY.md))

8. **Deployment Checklist**
   - Automatisierte Checks für alle Security Controls ([scripts/setup-hooks.sh](scripts/setup-hooks.sh), [.github/workflows/security-gates.yml](.github/workflows/security-gates.yml))

**Verification**
- Manuelle und automatisierte Tests:  
  - Netzwerkzugriff prüfen (nur VPN/SSH)
  - Secrets nur verschlüsselt im Repo
  - Container laufen als unprivilegierter User
  - Pre-Commit und CI/CD blockieren unsichere Commits
  - Monitoring und Alerts werden ausgelöst bei Vorfällen
- Security Checklist vor Deployment abarbeiten

**Decisions**
- Podman für Rootless-Container auf macOS statt Docker
- sops/age als Standard für Secrets Encryption
- Trivy/Syft/Cosign für Container Security
- GitHub Actions als zentrale CI/CD Security Gates
- Prometheus/Loki für Monitoring und Audit

Bitte Review: Gibt es spezielle Anforderungen, die noch nicht abgedeckt sind? Sollen bestimmte Controls priorisiert werden?
