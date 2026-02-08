# Infrastructure

This directory contains infrastructure configuration and deployment scripts.

## Docker Compose Files

### docker-compose.systems.yaml
Core system services (from `/systems`)

**Services:**
- PostgreSQL
- Redis
- n8n automation

**Usage:**
```bash
docker compose -f docker-compose.systems.yaml up -d
```

### docker-compose.atomic-reactor.yaml
Task orchestration system (from `/atomic-reactor`)

**Services:**
- Task runners
- Job schedulers

**Usage:**
```bash
docker compose -f docker-compose.atomic-reactor.yaml up -d
```

### docker-compose.openclaw.yaml
OpenClaw AI platform (from `/openclaw-config`)

**Services:**
- OpenClaw gateway
- Models
- Jobs

**Usage:**
```bash
docker compose -f docker-compose.openclaw.yaml up -d
```

## Quick Start

### Start All Services

```bash
cd infra

# Start core services
docker compose -f docker-compose.systems.yaml up -d

# Start atomic reactor
docker compose -f docker-compose.atomic-reactor.yaml up -d

# Check status
docker ps
```

### Stop All Services

```bash
docker compose -f docker-compose.systems.yaml down
docker compose -f docker-compose.atomic-reactor.yaml down
docker compose -f docker-compose.openclaw.yaml down
```

## Environment Variables

Copy `.env.example` to `.env` in the root directory and configure:

```bash
# From repository root
cp .env.example .env
# Edit .env with your values
```

## Networking

Services communicate via Docker network:
- Network name: `aiempire-network`
- Internal DNS resolution
- Isolated from host

## Volumes

Persistent data stored in Docker volumes:
- `postgres-data` - Database
- `redis-data` - Cache
- `n8n-data` - Workflows

## Port Mappings

| Service | Internal Port | External Port |
|---------|--------------|---------------|
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| n8n | 5678 | 5678 |
| OpenClaw | 18789 | 18789 |
| CRM | 3500 | 3500 |

## Monitoring

Check service health:

```bash
# View logs
docker compose -f docker-compose.systems.yaml logs -f

# Check specific service
docker compose -f docker-compose.systems.yaml logs -f postgres

# Service status
docker compose -f docker-compose.systems.yaml ps
```

## Troubleshooting

### Services won't start

```bash
# Check Docker daemon
docker info

# Check disk space
docker system df

# Clean up if needed
docker system prune -f
```

### Port conflicts

```bash
# Check what's using a port
lsof -i :5432

# Kill process if needed
kill -9 <PID>
```

### Data persistence issues

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect postgres-data

# Backup volume
docker run --rm -v postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data
```

## Backup & Restore

### Backup

```bash
# Backup all volumes
./scripts/backup-volumes.sh

# Or manually
docker compose -f docker-compose.systems.yaml down
docker run --rm -v postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data
docker compose -f docker-compose.systems.yaml up -d
```

### Restore

```bash
docker compose -f docker-compose.systems.yaml down
docker run --rm -v postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /
docker compose -f docker-compose.systems.yaml up -d
```

## Future Infrastructure

Planned additions:
- Kubernetes configurations
- Terraform scripts
- Ansible playbooks
- CI/CD deployment scripts
- Monitoring stack (Prometheus, Grafana)

## Best Practices

1. **Environment Variables** - Always use `.env`, never hardcode
2. **Version Control** - Track all config changes
3. **Documentation** - Update this README when changing infra
4. **Testing** - Test in dev before production
5. **Backups** - Regular automated backups
6. **Monitoring** - Set up alerts for failures
7. **Security** - Keep images updated, scan for vulnerabilities

## Resources

- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Infrastructure Runbooks](../docs/runbooks/infrastructure/)

---

**Maintained by**: Maurice Pfeifer
**Last Updated**: 2026-02-08
