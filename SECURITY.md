# Security & Secrets Policy

## 🔒 Overview

This document outlines security best practices for the AI Empire project.

## 🔑 Secrets Management

### What are Secrets?

Secrets include:
- API keys (OpenAI, Moonshot, Kimi, etc.)
- Database credentials
- Authentication tokens
- Private keys
- OAuth credentials
- Webhook URLs
- Service account credentials

### Rules

1. **NEVER commit secrets to the repository**
2. **Use environment variables** for all secrets
3. **Use `.env.example`** as a template (without actual values)
4. **Add `.env` to `.gitignore`**
5. **Rotate secrets** if accidentally committed

### Environment Variables

Store secrets in environment variables:

```bash
# .env (NEVER commit this file!)
OPENAI_API_KEY=sk-...
MOONSHOT_API_KEY=...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

Always provide a template:

```bash
# .env.example (commit this!)
OPENAI_API_KEY=your_openai_key_here
MOONSHOT_API_KEY=your_moonshot_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
```

### Loading Environment Variables

**Node.js:**
```javascript
require('dotenv').config();
const apiKey = process.env.OPENAI_API_KEY;
```

**Python:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
```

## 🚫 What NOT to Commit

Never commit:
- `.env` files
- `config.json` with secrets
- Private keys (`.pem`, `.key`, `.p12`)
- Database dumps with real data
- API credentials in code
- Hardcoded passwords
- Session tokens
- Backup files containing secrets

## ✅ Safe to Commit

Safe to commit:
- `.env.example` (templates)
- `config.example.json` (templates)
- Documentation
- Code without secrets
- Test fixtures (fake data)
- Public configuration

## 🔍 Checking for Secrets

### Pre-commit Check

Before committing, check for secrets:

```bash
# Search for common secret patterns
git grep -iE "(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}"

# Use git-secrets (recommended)
git secrets --scan
```

### CI/CD Scanning

We automatically scan for secrets using:
- **TruffleHog** - Finds secrets in code
- **Trivy** - Scans for vulnerabilities

### Manual Review

Before pushing:
1. Review `git diff`
2. Check for hardcoded values
3. Verify `.env` is not staged
4. Confirm `.gitignore` is correct

## 🆘 If You Commit a Secret

**Act immediately:**

1. **Rotate the secret** - Generate a new key/token
2. **Remove from history** (if just committed):
   ```bash
   git reset HEAD~1
   git add -u
   git commit -m "Remove sensitive data"
   ```
3. **For older commits**, use BFG Repo-Cleaner:
   ```bash
   # Install BFG
   # https://rtyley.github.io/bfg-repo-cleaner/
   
   # Remove secrets from history
   bfg --replace-text passwords.txt
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```
4. **Notify team** - Alert others who may have pulled
5. **Update documentation** - Document the incident

## 🔐 Access Control

### Principle of Least Privilege

- Only grant necessary permissions
- Use read-only access when possible
- Regularly audit access
- Remove access when no longer needed

### API Keys

- Use separate keys for dev/staging/production
- Set rate limits and quotas
- Monitor usage
- Rotate regularly (every 90 days)

### GitHub Secrets

Store secrets in GitHub Secrets (Settings → Secrets):
- `OPENAI_API_KEY`
- `MOONSHOT_API_KEY`
- `NPM_TOKEN`
- `DOCKER_HUB_TOKEN`

Access in workflows:
```yaml
env:
  API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## 🛡️ Security Best Practices

### Code Security

1. **Validate inputs** - Sanitize user input
2. **Escape outputs** - Prevent XSS attacks
3. **Use parameterized queries** - Prevent SQL injection
4. **Update dependencies** - Patch vulnerabilities
5. **Use HTTPS** - Encrypt data in transit

### Dependency Security

```bash
# Check for vulnerabilities
npm audit
pip-audit

# Update dependencies
npm update
pip install --upgrade
```

### Docker Security

1. **Don't run as root**
   ```dockerfile
   USER nonroot
   ```
2. **Use official base images**
3. **Scan images** with Trivy
4. **Keep images updated**
5. **Minimize image size**

## 📋 Security Checklist

Before deploying:

- [ ] No secrets in code
- [ ] `.env` in `.gitignore`
- [ ] `.env.example` created
- [ ] Dependencies updated
- [ ] Security scan passed
- [ ] Access controls reviewed
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Logging enabled
- [ ] Backups configured

## 🚨 Reporting Security Issues

Found a vulnerability?

**DON'T:**
- Open a public issue
- Post in discussions
- Share exploit code publicly

**DO:**
1. Email: [security contact to be added]
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
3. Wait for response before disclosure

We'll respond within:
- **24 hours** - Critical issues
- **72 hours** - High severity
- **1 week** - Medium/low severity

## 📚 Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-08 | Initial security policy | System |

---

**Remember: Security is everyone's responsibility!** 🔒
