# Merge Rules

## Allowed Merge Strategy

- Squash merge only.
- Merge commit and rebase merge are disabled.

## PR Requirements

- Every change must come via Pull Request.
- PR must describe scope, risk, and verification.
- PR should reference at least one issue when applicable.
- For non-trivial changes, require at least one approval before merge.

## Branch Hygiene

- Delete branch after merge is enabled.
- Keep PRs small and focused to one purpose.
- Close stale drafts that are no longer relevant.

## Automation Safety

- Workflows that auto-create issues must stay disabled unless explicitly re-approved.
- Any workflow with write permissions must document its side effects in the PR.
