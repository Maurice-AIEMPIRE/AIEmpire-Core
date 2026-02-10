# AI Empire - Run Commands

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Boot the Empire Nucleus
python -m ai_empire.empire_nucleus --boot

# Check health
python -m ai_empire.empire_nucleus --health

# Show status
python -m ai_empire.empire_nucleus --status

# List available skills
python -m ai_empire.empire_nucleus --skills
```

## Existing Workflow System (unchanged)

```bash
# Full 5-step compound loop
python workflow-system/orchestrator.py

# Single step
python workflow-system/orchestrator.py --step audit

# New weekly cycle
python workflow-system/orchestrator.py --new-cycle

# Check workflow status
python workflow-system/orchestrator.py --status
```

## Empire Control Center

```bash
# Full system status
python workflow-system/empire.py status

# Run workflow
python workflow-system/empire.py workflow

# Cowork daemon
python workflow-system/empire.py cowork --daemon --focus revenue

# Resource guard
python workflow-system/empire.py guard
```

## Safari Backdrop-Filter Fix

```bash
# Dry run - see what needs fixing
python scripts/fix_backdrop_filter.py

# Apply fixes
python scripts/fix_backdrop_filter.py --apply

# CI check mode (exit 1 if unfixed)
python scripts/fix_backdrop_filter.py --check
```

## Empire API (Mobile Command Center)

```bash
# Start API server (accessible from iPhone)
cd empire-api && pip install -r requirements.txt && python server.py
```

## Verification Commands

```bash
# Verify all core modules import
python -c "from ai_empire import __version__; print(f'v{__version__}')"

# Verify no NoneType issues
python -c "
from ai_empire.empire_nucleus import EmpireNucleus
n = EmpireNucleus()
print('All components initialized, no NoneType')
"

# Verify existing workflow system
cd workflow-system && python -c "
from state.context import load_state
from resource_guard import ResourceGuard
print(f'Cycle: {load_state().get(\"cycle\", 0)}')
print(f'Guard: {ResourceGuard().format_status()}')
"

# Check backdrop-filter compliance
python scripts/fix_backdrop_filter.py --check
```

## Skills

Skills are defined in `.claude/skills/*/SKILL.md`. To list:

```bash
python -m ai_empire.empire_nucleus --skills
```

Available skill categories:
- **Core**: nucleus, chief-of-staff
- **Revenue**: sales, marketing, seo, content
- **Operations**: ops-automation, qa, data-curation, templates-export
- **Legal War Room**: legal, legal-timeline, legal-evidence, legal-claims, legal-contracts, legal-procedure, legal-settlement, legal-opponent, legal-drafting, legal-risk, legal-qa
