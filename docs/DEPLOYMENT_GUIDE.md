# AI EMPIRE DEPLOYMENT GUIDE

**Version**: v1.0 (2026-02-10)
**Status**: Ready for Phase 1

## PRE-DEPLOYMENT CHECKLIST
- [ ] Secrets encrypted (sops/age)
- [ ] TLS certificates ready
- [ ] Firewall + VPN configured
- [ ] Backups tested
- [ ] Monitoring deployed

## STEP 1: SECRETS
```bash
brew install sops age
age-keygen -o ~/.age/keys.txt
sops --encrypt .env > .env.enc
```

## STEP 2: NETWORK
```bash
# Tailscale VPN
brew install tailscale && sudo tailscale up

# UFW (Linux)
sudo ufw default deny incoming
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp
sudo ufw enable
```

## STEP 3: DEPLOY
```bash
sops --decrypt .env.enc > .env.tmp && source .env.tmp
docker-compose up -d
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
rm .env.tmp
```

## STEP 4: VERIFY
```bash
curl -s http://localhost:3333/health | jq .
curl -s http://localhost:9090/-/healthy
```

## ROLLBACK
```bash
docker-compose down
docker-compose -f docker-compose.yml up -d
```

## SUCCESS CRITERIA
1. All services healthy
2. TLS valid
3. Monitoring active
4. Alerts configured
5. Secrets encrypted
6. Rollback tested
