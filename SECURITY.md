# Security Setup Guide

## ⚠️ CRITICAL: API Keys

This project uses sensitive API keys. **NEVER commit them to git.**

### Setup Instructions

1. **Copy the example config:**
   ```bash
   cp .env.example .env
   ```

2. **Get your Moonshot API Key:**
   - Go to https://platform.moonshot.cn/api-keys
   - Create or copy your API key
   - Add to `.env`:
     ```
     MOONSHOT_API_KEY=sk-your-key-here
     ```

3. **Get your GitHub Token (optional, for GitHub automation):**
   - Go to https://github.com/settings/tokens
   - Create token with `repo` and `workflow` scopes
   - Add to `.env`:
     ```
     GITHUB_TOKEN=ghp_your-token-here
     ```

4. **Load environment variables before running scripts:**
   ```bash
   # Option 1: Source .env manually
   source .env

   # Option 2: Use python-dotenv (recommended)
   # Scripts will auto-load .env if python-dotenv is installed
   pip install python-dotenv
   ```

### Verification

Before running any scripts, verify the environment is set:
```bash
echo $MOONSHOT_API_KEY  # Should print your key
```

## Files with Security Updates (Feb 2026)

✅ **Hardcoded API keys removed** from:
- `x-lead-machine/x_automation.py`
- `x-lead-machine/post_generator.py`
- `x-lead-machine/viral_reply_generator.py`
- `x-lead-machine/generate_week.py`
- `kimi-swarm/github_scanner_100k.py`
- `kimi-swarm/swarm_100k.py`
- `atomic-reactor/run_tasks.py`

✅ **Hardcoded paths fixed** in:
- `mission_control.py` - Now uses `GITHUB_WORKSPACE` env var
- `brain-system/orchestrator.py` - Updated health checks
- `kimi-swarm/swarm_100k.py` - Uses `OPENCLAW_HOME` env var

✅ **Error handling improved**:
- mission_control.py - Added proper exception types
- brain-system/orchestrator.py - Fixed bare except clauses

## What Each Environment Variable Does

| Variable | Purpose | Example |
|----------|---------|---------|
| `MOONSHOT_API_KEY` | Kimi LLM API access | `sk-...` |
| `GITHUB_TOKEN` | GitHub API automation | `ghp_...` |
| `GITHUB_REPO` | Repository path | `mauricepfeifer-ctrl/AIEmpire-Core` |
| `GITHUB_WORKSPACE` | Working directory in CI/CD | `/home/runner/work/...` |
| `OPENCLAW_HOME` | OpenClaw installation path | `~/.openclaw` |

## Security Checklist

- [ ] `.env` file created and filled with real values
- [ ] `.env` is in `.gitignore` (already is)
- [ ] Never run scripts without `MOONSHOT_API_KEY` set
- [ ] Never log or print `MOONSHOT_API_KEY`
- [ ] Run `git log --all --source -- '*MOONSHOT*'` to check no keys leaked
- [ ] If keys ever committed: rotate them immediately at https://platform.moonshot.cn/api-keys

## Testing Scripts

To verify everything works:

```bash
# Test mission control (no actual scan needed)
python mission_control.py

# Test brain system (health checks only)
python brain-system/orchestrator.py

# Test content generation
python x-lead-machine/x_automation.py
```

## Incident Response

If you accidentally commit a secret:

1. **Immediately rotate the key** at the service (Moonshot, GitHub, etc.)
2. **Remove from git history:**
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch .env' \
     -r HEAD
   ```
3. **Force push:** `git push -f`
4. **Notify the team**

---

**Last Updated:** 2026-02-10
**Security Officer:** Claude Code
**Status:** ✅ Hardcoded secrets REMOVED
