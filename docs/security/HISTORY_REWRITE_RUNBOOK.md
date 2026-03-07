# Git History Secret Cleanup Runbook

Last updated: 2026-02-19
Repository: Maurice-AIEMPIRE/AIEmpire-Core

## Why this is required

Secret-like values are still present in historical commits even though `main` has been redacted.
Public repository history is immutable for consumers until rewritten.

## Scope confirmed

The following key patterns were found in history:

- `sk-e57Q5aDfcpXpHkYfgeWCU3xjuqf2ZPoYxhuRH0kEZXGBeoMF`
- `sk-hMWtpmLkLxNsqTyVEiKimq5ypRDBjhJGNqngxqe6HvGP3o9Y`

Historical paths include:

- `kimi_swarm/github_scanner_100k.py`
- `x-lead-machine/post_generator.py`
- `x-lead-machine/viral_reply_generator.py`
- `x-lead-machine/generate_week.py`
- `x-lead-machine/x_automation.py`
- `atomic-reactor/run_tasks.py`
- `docs/CODEBASE_AUDIT_2026-02-09.md`
- `external/imports/AIEmpire-Core-main/...`

## Preconditions

- Rotate and revoke all exposed keys before rewriting history.
- Freeze merges and pushes while rewrite is in progress.
- Ensure admins are available for immediate force-push and branch protection restore.

## Step-by-step cleanup

1. Clone a fresh mirror.

```bash
git clone --mirror https://github.com/Maurice-AIEMPIRE/AIEmpire-Core.git
cd AIEmpire-Core.git
```

2. Create replacement rules.

```bash
cat > /tmp/replacements.txt <<'TXT'
sk-e57Q5aDfcpXpHkYfgeWCU3xjuqf2ZPoYxhuRH0kEZXGBeoMF==>REDACTED_MOONSHOT_KEY
sk-hMWtpmLkLxNsqTyVEiKimq5ypRDBjhJGNqngxqe6HvGP3o9Y==>REDACTED_MOONSHOT_KEY
TXT
```

3. Rewrite full history with `git-filter-repo`.

```bash
git filter-repo --replace-text /tmp/replacements.txt --force
```

4. Verify no leak signatures remain.

```bash
git grep -n -I -E 'sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}' $(git rev-list --all)
```

5. Temporarily relax branch protection only for rewrite push.

- Disable branch protection on `main`, or allow force-push for the admin performing the rewrite.

6. Force push rewritten history.

```bash
git push --force --mirror
```

7. Immediately re-apply protections.

- Require PRs
- Require 1 approval
- Require CODEOWNERS review
- Require conversation resolution
- Disable force push and deletion

8. Post-rewrite cleanup.

- Ask collaborators to reclone or hard reset to new history.
- Invalidate old commit SHAs in docs/automation references.
- Re-run secret scans (`Secret Scan` workflow + GitHub secret scanning alerts).

## Rollback strategy

- Keep a temporary backup mirror before the rewrite.
- If rewrite causes critical disruption, push backup mirror to a temporary archive repo for comparison.

## Ownership

- Security owner: @mauricepfeifer-ctrl
- Change window: maintenance window only, no active PR merges
