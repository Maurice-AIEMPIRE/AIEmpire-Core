# Docker Cleanup Runbook

## Quick Fix
```bash
docker system prune -f
docker system df
```

## Complete Cleanup
```bash
docker compose down
docker system prune -a --volumes -f
docker compose up -d
```

## Prevention
Weekly cron: `0 2 * * 0 docker system prune -f`
