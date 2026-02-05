from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from automation.core.runner import RunResult, Runner
from automation.utils.files import backup_file, ensure_dir, read_text, timestamp_id, write_text


ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = ROOT / "content_factory" / "prompts"
DELIVERABLES_DIR = ROOT / "content_factory" / "deliverables"


def render_prompt(template_path: Path, variables: Dict[str, str], extra_input: Optional[str] = None) -> str:
    template = read_text(template_path)
    for key, value in variables.items():
        template = template.replace("{" + key + "}", value)
    if extra_input:
        template = template.strip() + "\n\nZUSATZ-INPUT:\n" + extra_input.strip() + "\n"
    return template


def extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if line.strip().lower().startswith(heading.lower() + ":"):
            start_idx = idx + 1
            break
    if start_idx is None:
        return text
    section_lines = []
    for line in lines[start_idx:]:
        if re.match(r"^[A-ZÄÖÜ][A-ZÄÖÜ0-9 _-]+:\s*$", line.strip()):
            break
        section_lines.append(line)
    return "\n".join(section_lines)


def extract_list(text: str, heading: str) -> List[str]:
    section = extract_section(text, heading)
    items: List[str] = []
    for line in section.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^\d+[\).]\s*(.+)", line)
        if match:
            items.append(match.group(1).strip())
        else:
            items.append(line)
    return items


def chunk(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def format_numbered(items: List[str]) -> str:
    return "\n".join(f"{idx + 1}) {item}" for idx, item in enumerate(items))


def gather_ideation(
    runner: Runner,
    variables: Dict[str, str],
    target_hooks: int,
    target_topics: int,
) -> Tuple[List[str], List[str]]:
    hooks: List[str] = []
    topics: List[str] = []
    prompt_path = PROMPTS_DIR / "ideation.md"
    while len(hooks) < target_hooks or len(topics) < target_topics:
        remaining_hooks = max(0, target_hooks - len(hooks))
        remaining_topics = max(0, target_topics - len(topics))
        batch_hooks = min(remaining_hooks, 30) if remaining_hooks > 0 else 0
        batch_topics = min(remaining_topics, 20) if remaining_topics > 0 else 0
        parts = []
        if batch_hooks > 0:
            parts.append(f"{batch_hooks} Hooks")
        else:
            parts.append("maximal 5 Hooks")
        if batch_topics > 0:
            parts.append(f"{batch_topics} Themenideen")
        else:
            parts.append("maximal 5 Themenideen")
        extra = "Bitte liefere " + " und ".join(parts) + "."
        prompt = render_prompt(prompt_path, variables, extra_input=extra)
        result = runner.run_task("ideation", prompt)
        hooks.extend(extract_list(result.text, "HOOKS"))
        topics.extend(extract_list(result.text, "THEMEN"))
        if not runner.execute:
            break
    return hooks[:target_hooks], topics[:target_topics]


def run_writer_batches(
    runner: Runner,
    task_type: str,
    template_name: str,
    variables: Dict[str, str],
    items: List[str],
    batch_size: int,
    refiner: bool = True,
) -> str:
    template_path = PROMPTS_DIR / template_name
    refiner_path = PROMPTS_DIR / "refiner.md"
    outputs: List[str] = []
    for batch in chunk(items, batch_size):
        label = "HOOKS" if "tweets" in template_name else "THEMEN"
        extra = f"{label}:\n" + format_numbered(batch)
        prompt = render_prompt(template_path, variables, extra_input=extra)
        result = runner.run_task(task_type, prompt)
        text = result.text
        if refiner:
            ref_prompt = render_prompt(refiner_path, {"STIL": variables["STIL"]}, extra_input=f"DRAFTS:\n{text}")
            refined = runner.run_task("refiner", ref_prompt)
            if refined.text:
                text = refined.text
        outputs.append(text)
    return "\n\n".join(outputs)


def write_deliverable(runner: Runner, filename: str, content: str) -> str:
    if runner.execute:
        target = DELIVERABLES_DIR / filename
        backup_dir = DELIVERABLES_DIR / f"backup_{timestamp_id()}"
        backup_file(target, backup_dir)
        write_text(target, content)
        return str(target)
    target = ROOT / "automation" / "runs" / f"dryrun_{runner.run_id}" / filename
    write_text(target, content)
    return str(target)


def run_threads(runner: Runner, variables: Dict[str, str], count: int) -> str:
    hooks, topics = gather_ideation(runner, variables, target_hooks=10, target_topics=count)
    output = run_writer_batches(
        runner,
        task_type="writer_threads",
        template_name="writer_threads.md",
        variables=variables,
        items=topics,
        batch_size=5,
        refiner=True,
    )
    return write_deliverable(runner, "threads_50.md", output)


def run_tweets(runner: Runner, variables: Dict[str, str], count: int) -> str:
    hooks, topics = gather_ideation(runner, variables, target_hooks=count, target_topics=10)
    output = run_writer_batches(
        runner,
        task_type="writer_tweets",
        template_name="writer_tweets.md",
        variables=variables,
        items=hooks,
        batch_size=10,
        refiner=True,
    )
    return write_deliverable(runner, "tweets_300.md", output)


def run_premium_prompts(runner: Runner, variables: Dict[str, str], count: int) -> str:
    template_path = PROMPTS_DIR / "writer_premium_prompts.md"
    extra = f"Ziel: Erstelle insgesamt {count} Premium-Prompts."
    prompt = render_prompt(template_path, variables, extra_input=extra)
    result = runner.run_task("writer_premium", prompt)
    output = result.text
    refiner_path = PROMPTS_DIR / "refiner.md"
    ref_prompt = render_prompt(refiner_path, {"STIL": variables["STIL"]}, extra_input=f"DRAFTS:\n{output}")
    refined = runner.run_task("refiner", ref_prompt)
    if refined.text:
        output = refined.text
    return write_deliverable(runner, "premium_prompts_400.md", output)


def run_monetization(runner: Runner, variables: Dict[str, str]) -> str:
    template_path = PROMPTS_DIR / "strategy.md"
    prompt = render_prompt(template_path, variables)
    result = runner.run_task("strategy", prompt)
    return write_deliverable(runner, "monetization_strategy.md", result.text)


def run_full(runner: Runner, variables: Dict[str, str], targets: Dict[str, int]) -> List[str]:
    paths = []
    paths.append(run_threads(runner, variables, targets.get("threads", 50)))
    paths.append(run_tweets(runner, variables, targets.get("tweets", 300)))
    paths.append(run_premium_prompts(runner, variables, targets.get("premium_prompts", 400)))
    paths.append(run_monetization(runner, variables))
    return paths
