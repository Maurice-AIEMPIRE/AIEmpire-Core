# Contributing to AI Empire

Welcome to AI Empire! This guide will help you contribute effectively to the project.

## 🎯 Workflow Overview

We use GitHub as our "Single Source of Truth" - everything flows through Issues → PRs → Releases.

```
Issue Created → Branch → Development → PR → Review → Merge → Release
```

## 📋 Creating Issues

We use **atomic tasks** - small, measurable, independent units of work.

### Issue Types

1. **🎯 Atomic Task** - Small, focused development task
2. **🐛 Bug Report** - Report bugs or unexpected behavior
3. **✨ Feature Request** - Suggest new features
4. **💰 Revenue Opportunity** - Track revenue-generating ideas

### Issue Templates

Use the provided templates - they ensure you include all necessary information:
- Goal/Problem
- Acceptance Criteria
- Constraints
- Tests & Verification

### Labels

Issues are automatically labeled for routing:

**Categories:**
- `code` - Code changes
- `docs` - Documentation
- `research` - Research tasks
- `ops` - Operations
- `security` - Security
- `growth` - Growth/marketing
- `revenue` - Revenue generation

**Priority:**
- `P0` - Critical/Blocking
- `P1` - High/Important
- `P2` - Medium/Nice-to-have

## 🔀 Pull Requests

### PR Guidelines

1. **Keep PRs small** - Max 200-400 lines of changes
2. **One concern per PR** - Don't mix features and bug fixes
3. **Use the PR template** - Fill out all sections
4. **Link to issues** - Use "Closes #123" syntax

### PR Template Sections

- **Problem** - What are you solving?
- **Solution** - How did you solve it?
- **Changes Made** - List key changes
- **Risk Assessment** - What could go wrong?
- **Tests & Verification** - How was it tested?
- **Rollback Plan** - How to revert if needed?

### Branch Naming

Use conventional naming:
- `feature/add-authentication`
- `fix/crm-login-bug`
- `docs/update-readme`
- `ops/docker-optimization`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user authentication to CRM
fix: resolve login timeout issue
docs: update installation guide
chore: bump version to 1.2.0
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Test additions/changes
- `chore` - Build/tooling changes

## 🧪 Testing

### Before Submitting PR

1. Run linters: `npm run lint` or `flake8`
2. Run tests: `npm test` or `pytest`
3. Build check: Validate Docker Compose files
4. Security scan: Check for secrets/vulnerabilities

### CI Pipeline

All PRs run through automated checks:
- **Lint** - Code style validation
- **Tests** - Unit and integration tests
- **Build** - Compilation/validation
- **Security** - Secret and vulnerability scanning

## 🔒 Security

### Secrets Management

- **NEVER** commit secrets to the repository
- Use `.env.example` for template files
- Add sensitive files to `.gitignore`
- Use environment variables for secrets

### Reporting Security Issues

Found a vulnerability? Please:
1. **Don't** open a public issue
2. Email: [security contact]
3. Include details but not exploit code

## 📚 Documentation

### When to Update Docs

Update documentation when you:
- Add new features
- Change existing behavior
- Add new configuration options
- Create new tools/scripts

### Documentation Structure

```
/docs
├── SYSTEM_ARCHITECTURE.md    - System overview
├── CHATGPT_TASKS.md          - Task management
└── runbooks/                 - Operational guides
```

## 🚀 Release Process

### Versioning

We use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes

### Creating Releases

1. Tag release: `git tag v1.2.3`
2. Push tag: `git push origin v1.2.3`
3. GitHub Actions automatically:
   - Generates changelog
   - Creates release notes
   - Builds artifacts

## 🎓 Definition of Done

A task is complete when:
- [ ] Tests are passing
- [ ] Documentation is updated
- [ ] Changelog entry added (if applicable)
- [ ] Security check passed
- [ ] Code review completed
- [ ] PR approved and merged

## 💡 Best Practices

### Code Quality

- Write clear, self-documenting code
- Add comments for complex logic only
- Follow existing code style
- Keep functions small and focused

### Communication

- Be respectful and constructive
- Ask questions if unclear
- Document decisions in issues/PRs
- Update issue status regularly

### Time Management

- Break large tasks into small issues
- Update progress frequently
- Don't let PRs sit for days
- Ask for help when stuck

## 🛠️ Development Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- Git

### Quick Start

```bash
# Clone repository
git clone https://github.com/mauricepfeifer-ctrl/AIEmpire-Core.git
cd AIEmpire-Core

# Install dependencies
cd crm && npm install

# Run tests
npm test

# Start services
docker compose up
```

## 🤝 Community

- **Discussions** - Ask questions, share ideas
- **Issues** - Report bugs, request features
- **PRs** - Contribute code
- **Wiki** - Learn about the project

## 📜 Code of Conduct

- Be professional and respectful
- Welcome newcomers
- Focus on constructive feedback
- Celebrate successes

## 🙋 Need Help?

- Check existing issues and discussions
- Read the documentation
- Ask in GitHub Discussions
- Reach out to maintainers

---

Thank you for contributing to AI Empire! 🚀
