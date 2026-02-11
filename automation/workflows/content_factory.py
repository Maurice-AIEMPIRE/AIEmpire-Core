from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from automation.core.runner import RunResult, Runner
from automation.utils.files import backup_file, ensure_dir, read_text, timestamp_id, write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = ROOT / "content_factory" / "prompts"
DELIVERABLES_DIR = ROOT / "content_factory" / "deliverables"
X_TEMPLATES_DIR = DELIVERABLES_DIR / "x_templates"
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)[\).]\s*(.+?)\s*$")
CREATIVE_LANES = [
    "comedy_ai",
    "ai_cartoon",
    "comic_caricature",
    "dark_humor_ai",
]


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


def extract_numbered_posts(text: str) -> List[str]:
    posts: List[str] = []
    seen = set()
    for line in text.splitlines():
        match = NUMBERED_LINE_RE.match(line)
        if not match:
            continue
        post = match.group(2).strip()
        if not post:
            continue
        normalized = re.sub(r"\s+", " ", post).strip().lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        posts.append(post)
    return posts


def build_visual_prompt(post: str, lane: str) -> str:
    base = re.sub(r"\s+", " ", post).strip()
    if len(base) > 180:
        base = base[:177].rstrip() + "..."
    if lane == "comedy_ai":
        prefix = "Single-panel comedy scene about daily AI workflow chaos."
    elif lane == "ai_cartoon":
        prefix = "AI cartoon scene with clear visual metaphor and playful contrast."
    elif lane == "comic_caricature":
        prefix = "Satirical comic caricature with exaggerated office-tech characters."
    else:
        prefix = "Dark-humor AI comic with ironic tension, no hate and no violence."
    return (
        f"{prefix} Core idea: {base}. Style: clean line art, high contrast, "
        "editorial look, no text overlay."
    )


def build_templates_markdown(payload: Dict[str, object]) -> str:
    templates = payload.get("templates", [])
    lines: List[str] = [
        "# X Template Pack",
        "",
        f"- run_id: {payload.get('run_id', '')}",
        f"- created_at: {payload.get('created_at', '')}",
        f"- creative_mode: {payload.get('creative_mode', '')}",
        f"- niche: {payload.get('niche', '')}",
        f"- count: {payload.get('template_count', 0)}",
        "",
    ]
    if not isinstance(templates, list) or not templates:
        lines.append("No numbered X posts were extracted from this run.")
        lines.append("")
        return "\n".join(lines)

    for item in templates:
        if not isinstance(item, dict):
            continue
        lines.append(f"## {item.get('id', '')}")
        lines.append(f"- lane: {item.get('lane', '')}")
        lines.append(f"- status: {item.get('status', '')}")
        lines.append(f"- post: {item.get('post', '')}")
        lines.append(f"- visual_prompt: {item.get('visual_prompt', '')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_x_templates(
    runner: Runner,
    variables: Dict[str, str],
    generated_text: str,
) -> Optional[str]:
    posts = extract_numbered_posts(generated_text)
    created_at = dt.datetime.now().replace(microsecond=0).isoformat()
    creative_mode = variables.get("KREATIV_MODUS", "comedy_ai_cartoons_dark_humor_comic")

    templates = []
    for idx, post in enumerate(posts, start=1):
        lane = CREATIVE_LANES[(idx - 1) % len(CREATIVE_LANES)]
        templates.append(
            {
                "id": f"x_template_{idx:03d}",
                "post": post,
                "lane": lane,
                "visual_prompt": build_visual_prompt(post, lane),
                "status": "pending_review",
            }
        )

    payload: Dict[str, object] = {
        "run_id": runner.run_id,
        "created_at": created_at,
        "creative_mode": creative_mode,
        "niche": variables.get("NISCHE", ""),
        "style": variables.get("STIL", ""),
        "template_count": len(templates),
        "templates": templates,
    }

    ensure_dir(X_TEMPLATES_DIR)
    json_path = X_TEMPLATES_DIR / f"x_templates_{runner.run_id}.json"
    md_path = X_TEMPLATES_DIR / f"x_templates_{runner.run_id}.md"
    latest_json_path = X_TEMPLATES_DIR / "latest.json"
    latest_md_path = X_TEMPLATES_DIR / "latest.md"

    write_json(json_path, payload)
    write_json(latest_json_path, payload)
    markdown = build_templates_markdown(payload)
    write_text(md_path, markdown)
    write_text(latest_md_path, markdown)
    return str(md_path)


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
    deliverable_path = write_deliverable(runner, "tweets_300.md", output)
    write_x_templates(runner, variables, output)
    return deliverable_path


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
