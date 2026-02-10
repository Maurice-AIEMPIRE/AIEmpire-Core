#!/usr/bin/env python3
"""
PR Bot – Creates structured PR descriptions for agent branches.
Usage: python3 antigravity/pr_bot.py --open 4
"""
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rich.console import Console
from antigravity.config import PROJECT_ROOT
console = Console()

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=60)
    return r.returncode, (r.stdout + r.stderr).strip()

def get_agent_branches():
    _, out = run("git branch --list 'agent/*' 2>/dev/null")
    return [b.strip().lstrip("* ") for b in out.split("\n") if b.strip()]

def generate_pr_body(branch):
    _, diff_stat = run(f"git diff main...{branch} --stat 2>/dev/null")
    _, log = run(f"git log main..{branch} --oneline 2>/dev/null")
    agent = branch.split("/")[1] if "/" in branch else "unknown"
    return f"""## 🤖 Agent: {agent.upper()}
**Branch:** `{branch}`
**Generated:** {time.strftime('%Y-%m-%d %H:%M')}

### Changes
```
{diff_stat[:1000]}
```

### Commits
{log[:500]}

### Checks
- [ ] `python3 -m compileall . -q`
- [ ] `ruff check .`
- [ ] `pytest -q`
- [ ] No regressions
"""

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", type=int, default=4)
    args = parser.parse_args()

    branches = get_agent_branches()[:args.open]
    if not branches:
        console.print("[yellow]No agent branches.[/yellow]")
        return

    for br in branches:
        body = generate_pr_body(br)
        pr_file = Path(PROJECT_ROOT) / "antigravity" / "_reports" / f"pr_{br.replace('/','_')}.md"
        pr_file.parent.mkdir(parents=True, exist_ok=True)
        pr_file.write_text(body)
        console.print(f"[green]✓[/green] PR for {br} → {pr_file}")

if __name__ == "__main__":
    main()
