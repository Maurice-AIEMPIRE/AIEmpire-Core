# Claude x GitHub Workflow Guide

## Overview

This guide describes the optimal workflow for using Claude with GitHub to build and maintain the AI Empire.

## Core Concept: Atomic Tasks

**Atomic Task** = Small, measurable, independent unit of work that Claude can complete in one session.

### Characteristics
- **Small**: 50-400 lines of code changes max
- **Measurable**: Clear acceptance criteria
- **Independent**: No blocking dependencies
- **Testable**: Can be verified immediately
- **Reversible**: Easy to rollback if needed

## The Golden Workflow

```
┌─────────────────────────────────────────┐
│  1. Issue Created (Atomic Task)         │
│     - Clear goal                        │
│     - Acceptance criteria               │
│     - Constraints                       │
│     - Tests required                    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  2. Claude Gets Context                 │
│     - Repo structure                    │
│     - Issue details                     │
│     - Constraints (security, tests)     │
│     - Related code                      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  3. Claude Works in Branch              │
│     - feature/task-name                 │
│     - Small, focused changes            │
│     - Tests added/updated               │
│     - Docs updated                      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  4. Pull Request Created                │
│     - Uses PR template                  │
│     - Links to issue                    │
│     - Explains changes                  │
│     - Risk assessment                   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  5. GitHub Actions Run                  │
│     ✓ Lint code                        │
│     ✓ Run tests                        │
│     ✓ Security scan                    │
│     ✓ Build check                      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  6. Review & Merge                      │
│     - Manual review (optional)          │
│     - Merge to main                     │
│     - Auto-close issue                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  7. Deploy & Monitor                    │
│     - Auto-release (on tags)            │
│     - Changelog generated               │
│     - Monitor for issues                │
└─────────────────────────────────────────┘
```

## Step-by-Step Guide

### Step 1: Create Atomic Task

**Using GitHub UI:**

1. Go to Issues → New Issue
2. Select "🎯 Atomic Task" template
3. Fill in all sections:
   - **Goal**: What to achieve
   - **Acceptance Criteria**: How to verify success
   - **Constraints**: Limitations
   - **Tests**: How to test

**Example Good Task:**

```markdown
Goal: Add email validation to CRM lead form

Acceptance Criteria:
- [ ] Email format validated before saving
- [ ] Display error message for invalid emails
- [ ] Existing valid emails still work
- [ ] Tests added for validation logic

Constraints:
- Use existing validation library
- No new dependencies
- Max 100 lines changed

Tests:
- Unit tests for validation function
- Integration test for form submission
- Manual test with invalid emails
```

**Example Bad Task** (too broad):

```markdown
Goal: Improve CRM system

Acceptance Criteria:
- Make it better
- Fix all bugs
- Add features users want
```

### Step 2: Provide Context to Claude

When asking Claude to work on the task:

```markdown
I need you to work on Issue #123: Add email validation to CRM

Repository: mauricepfeifer-ctrl/AIEmpire-Core
Branch: feature/email-validation

Context:
- CRM is in /crm directory
- Using Node.js + Express
- SQLite database
- No test framework yet (just add manual verification)

Constraints:
- Keep changes minimal
- Don't break existing functionality
- Use validator.js if needed

Please:
1. Review the code structure
2. Implement email validation
3. Update the form handling
4. Test manually
5. Create PR
```

### Step 3: Claude Works in Branch

Claude will:

1. **Explore** the codebase
2. **Plan** the minimal changes
3. **Implement** the changes
4. **Test** the implementation
5. **Document** if needed
6. **Report progress** via commits

You should see commits like:
```
feat: add email validation to lead form
test: add validation tests
docs: update README with validation info
```

### Step 4: Create Pull Request

Claude creates PR using template:

```markdown
## Problem
Lead form accepts invalid emails, causing issues downstream.

Closes #123

## Solution
Added email validation using validator.js library:
- Validate on client side (immediate feedback)
- Validate on server side (security)
- Display clear error messages

## Changes Made
- Added validator.js dependency
- Updated form validation in server.js
- Added error display in HTML
- Added unit tests

## Risk Assessment
Breaking Changes: No
Risk Level: Low

Potential Issues:
- Existing invalid emails in DB (won't affect)
- New validation might be too strict (can adjust)

## Tests & Verification
- [x] Unit tests passing
- [x] Manual testing with invalid emails
- [x] Existing functionality works
- [x] Error messages display correctly

## Rollback Plan
1. Revert commit abc123
2. Restart server
3. Form works as before
```

### Step 5: GitHub Actions Run

Automatic checks:

**Lint**:
```bash
npm run lint  # Check code style
flake8        # Python linting
```

**Tests**:
```bash
npm test      # Run tests
pytest        # Python tests
```

**Security**:
```bash
trivy scan    # Vulnerability scan
trufflehog    # Secret scan
```

**Build**:
```bash
docker compose config  # Validate Docker files
python -m json.tool    # Validate JSON
```

If any check fails:
1. Review the error
2. Fix the issue
3. Push new commit
4. Checks run again

### Step 6: Review & Merge

**Manual Review Checklist**:
- [ ] Changes match issue description
- [ ] Code is clean and readable
- [ ] Tests are comprehensive
- [ ] Documentation updated
- [ ] No obvious bugs
- [ ] Security looks good

**Merge Options**:
1. **Squash and merge** (recommended) - Clean history
2. **Merge commit** - Preserve all commits
3. **Rebase and merge** - Linear history

After merge:
- Issue auto-closes (via "Closes #123")
- Branch can be deleted
- Changes are in main branch

### Step 7: Deploy & Monitor

**Automatic on Tag**:

```bash
git tag v1.2.3
git push origin v1.2.3
```

This triggers:
1. Changelog generation
2. Release notes creation
3. Docker image build (if applicable)
4. Version bump

**Monitoring**:
- Check application logs
- Monitor error rates
- Verify feature works in production
- Watch for user feedback

## Advanced Patterns

### Pattern 1: Feature Flags

For risky changes, use feature flags:

```javascript
if (process.env.ENABLE_EMAIL_VALIDATION === 'true') {
  // New validation logic
} else {
  // Old logic
}
```

Deploy with flag OFF, test, then enable.

### Pattern 2: Phased Rollout

1. Deploy to staging
2. Test thoroughly
3. Deploy to 10% of users
4. Monitor for issues
5. Deploy to 100%

### Pattern 3: Parallel Change

For breaking changes:

1. Add new code alongside old
2. Migrate gradually
3. Remove old code when safe

### Pattern 4: Reverting

If something breaks:

```bash
# Revert last commit
git revert HEAD

# Or revert specific commit
git revert abc123

# Push revert
git push origin main
```

This creates new commit that undoes changes.

## Best Practices

### For Creating Issues

✅ **Do**:
- Be specific about goal
- Include clear acceptance criteria
- List constraints
- Specify how to test
- Link related issues

❌ **Don't**:
- Make tasks too large
- Be vague about success
- Forget about testing
- Mix multiple concerns
- Skip documentation

### For Pull Requests

✅ **Do**:
- Keep changes small (<400 lines)
- Use PR template
- Link to issue
- Explain risks
- Add rollback plan
- Update docs

❌ **Don't**:
- Mix features and bugs
- Skip the template
- Make unrelated changes
- Forget tests
- Rush the merge

### For Commits

✅ **Do**:
- Use Conventional Commits
- Write clear messages
- Commit often
- Keep commits focused

❌ **Don't**:
- Commit secrets
- Make giant commits
- Use vague messages
- Mix concerns

**Good Commit Messages**:
```
feat: add email validation to lead form
fix: resolve timeout issue in API call
docs: update installation guide
test: add validation unit tests
chore: upgrade dependencies
```

**Bad Commit Messages**:
```
update
fix stuff
changes
wip
asdf
```

## Troubleshooting

### Issue: CI Fails on Lint

```bash
# Run locally first
npm run lint

# Fix issues
npm run lint:fix

# Commit fix
git add .
git commit -m "style: fix linting errors"
git push
```

### Issue: Tests Failing

```bash
# Run tests locally
npm test

# Debug specific test
npm test -- --grep "email validation"

# Fix code
# Commit and push
```

### Issue: Merge Conflicts

```bash
# Update your branch
git checkout feature/your-feature
git fetch origin
git rebase origin/main

# Resolve conflicts
# Edit conflicted files
git add .
git rebase --continue

# Push (force needed after rebase)
git push -f origin feature/your-feature
```

### Issue: Secrets Leaked

```bash
# 1. Rotate the secret immediately
# 2. Remove from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force push (dangerous!)
git push origin --force --all

# Better: Use BFG Repo-Cleaner
```

## Metrics to Track

### Velocity
- Issues closed per week
- Average time to close
- PR merge rate

### Quality
- Test coverage %
- Bug rate
- Revert rate

### Efficiency
- Cycle time (issue → merge)
- Review time
- Build time

## Tools & Resources

### GitHub Features
- [Issues](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/issues)
- [Pull Requests](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/pulls)
- [Actions](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/actions)
- [Projects](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/projects)

### Documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [SECURITY.md](../SECURITY.md)
- [STRUCTURE.md](../STRUCTURE.md)
- [GitHub Projects Setup](GITHUB_PROJECTS_SETUP.md)

### External Resources
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Semantic Versioning](https://semver.org/)

## Quick Reference

### Common Commands

```bash
# Start new feature
git checkout -b feature/task-name

# Check status
git status
git diff

# Commit changes
git add .
git commit -m "feat: add feature"

# Push branch
git push -u origin feature/task-name

# Update branch
git fetch origin
git rebase origin/main

# Clean up
git branch -d feature/task-name
```

### Issue Template Shortcuts

- `#` - Link to issue
- `@username` - Mention user
- `Closes #123` - Auto-close on merge
- `Fixes #123` - Same as Closes
- `Resolves #123` - Same as Closes

---

**Remember**: The goal is atomic, reversible, testable changes that Claude can deliver reliably. Small PRs = Fast reviews = Quick iterations = Faster shipping! 🚀
