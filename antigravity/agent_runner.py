"""
Agent Runner
=============
Executes a single Godmode Programmer agent with task context.
Handles branching, execution, and result collection.
"""

import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from antigravity.config import AgentConfig, MERGE_CHECKS, PROJECT_ROOT
from antigravity.ollama_client import OllamaClient, get_client

console = Console()


@dataclass
class AgentResult:
    """Result from a single agent run."""
    agent_name: str
    role: str
    model: str
    success: bool
    content: str
    tokens_used: int = 0
    duration_seconds: float = 0.0
    branch: Optional[str] = None
    files_changed: list = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "role": self.role,
            "model": self.model,
            "success": self.success,
            "content": self.content[:2000],  # truncate for storage
            "tokens_used": self.tokens_used,
            "duration_seconds": self.duration_seconds,
            "branch": self.branch,
            "files_changed": self.files_changed,
            "error": self.error,
        }


def _run_shell(cmd: str, cwd: str = PROJECT_ROOT) -> tuple[int, str]:
    """Run a shell command and return (returncode, output)."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr
    return result.returncode, output.strip()


def _create_branch(agent: AgentConfig, task_id: str) -> str:
    """Create and checkout a new branch for this agent run."""
    branch_name = f"{agent.branch_prefix}/{task_id}"

    # Stash any uncommitted changes
    _run_shell("git stash --quiet 2>/dev/null || true")

    # Create branch from current HEAD
    _run_shell(f"git checkout -b {branch_name} 2>/dev/null || git checkout {branch_name}")

    return branch_name


def _switch_back_to_main():
    """Switch back to main/master branch."""
    _run_shell("git checkout main 2>/dev/null || git checkout master 2>/dev/null || true")
    _run_shell("git stash pop --quiet 2>/dev/null || true")


def run_agent(
    agent: AgentConfig,
    task: str,
    context: Optional[str] = None,
    task_id: Optional[str] = None,
    use_branch: bool = True,
    client: Optional[OllamaClient] = None,
) -> AgentResult:
    """
    Run a single Godmode Programmer agent.

    Args:
        agent: Agent configuration
        task: The task description
        context: Optional file contents / error logs
        task_id: Optional task identifier for branch naming
        use_branch: Whether to create a git branch
        client: Optional OllamaClient (uses default if not provided)

    Returns:
        AgentResult with the agent's output
    """
    if client is None:
        client = get_client()

    if task_id is None:
        task_id = f"task-{int(time.time())}"

    console.print(Panel(
        f"[bold cyan]🚀 Agent: {agent.name}[/bold cyan]\n"
        f"[dim]Model: {agent.model}[/dim]\n"
        f"[dim]Task: {task[:100]}...[/dim]",
        title="[bold]GODMODE PROGRAMMER[/bold]",
        border_style="cyan"
    ))

    # Create branch if needed
    branch = None
    if use_branch:
        try:
            branch = _create_branch(agent, task_id)
            console.print(f"  [green]✓[/green] Branch: {branch}")
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Branch creation failed: {e}")

    # Run the agent
    start = time.time()
    try:
        result = client.chat(agent=agent, user_message=task, context=context)
        duration = time.time() - start

        content = result["content"]
        tokens = result["usage"]["total_tokens"]

        console.print(f"  [green]✓[/green] Response: {len(content)} chars, {tokens} tokens, {duration:.1f}s")

        # Parse any file changes from the response
        files_changed = _extract_files_from_response(content)

        agent_result = AgentResult(
            agent_name=agent.name,
            role=agent.role,
            model=agent.model,
            success=True,
            content=content,
            tokens_used=tokens,
            duration_seconds=duration,
            branch=branch,
            files_changed=files_changed,
        )

    except Exception as e:
        duration = time.time() - start
        console.print(f"  [red]✗[/red] Error: {e}")
        agent_result = AgentResult(
            agent_name=agent.name,
            role=agent.role,
            model=agent.model,
            success=False,
            content="",
            duration_seconds=duration,
            branch=branch,
            error=str(e),
        )

    # Switch back to main
    if use_branch:
        _switch_back_to_main()

    return agent_result


def _extract_files_from_response(content: str) -> list[str]:
    """Try to extract file paths mentioned in agent response."""
    files = []
    for line in content.split("\n"):
        line = line.strip()
        # Look for file paths
        if "/" in line and ("." in line.split("/")[-1]):
            # Heuristic: lines that look like file paths
            for word in line.split():
                word = word.strip("`\"'(),[]{}:")
                if "/" in word and "." in word.split("/")[-1] and len(word) < 200:
                    if not word.startswith("http"):
                        files.append(word)
    return list(set(files))[:20]  # dedupe and limit


def run_merge_checks(branch: Optional[str] = None) -> dict:
    """
    Run all merge gate checks.

    Returns:
        dict with: {passed: bool, results: [{check, passed, output}]}
    """
    console.print("\n[bold yellow]🔒 MERGE GATE CHECKS[/bold yellow]")

    results = []
    all_passed = True

    for check_cmd in MERGE_CHECKS:
        rc, output = _run_shell(check_cmd)
        passed = rc == 0
        if not passed:
            all_passed = False

        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        console.print(f"  {status} {check_cmd}")
        if not passed and output:
            # Show first 5 lines of error
            for line in output.split("\n")[:5]:
                console.print(f"    [dim]{line}[/dim]")

        results.append({
            "check": check_cmd,
            "passed": passed,
            "output": output[:500],
        })

    verdict = "[bold green]✅ ALL CHECKS PASSED[/bold green]" if all_passed else "[bold red]❌ MERGE BLOCKED[/bold red]"
    console.print(f"\n  {verdict}\n")

    return {"passed": all_passed, "results": results}
