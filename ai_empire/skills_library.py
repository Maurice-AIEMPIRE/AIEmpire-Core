"""
Skills Library - Filesystem-Based Skill Loading.

Skills are defined as directories containing a SKILL.md file
that describes the skill's purpose, triggers, inputs/outputs,
and step-by-step playbook.

Layout:
    .claude/skills/
        nucleus/SKILL.md
        legal/SKILL.md
        sales/SKILL.md
        ...

Usage:
    library = SkillsLibrary()
    skills = library.list_skills()
    skill = library.load_skill("legal")
    matched = library.match_skill("help me draft a contract")
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"
REPO_SKILLS_DIR = Path(__file__).parent.parent / ".claude" / "skills"


@dataclass
class Skill:
    """A loaded skill definition."""
    name: str
    path: Path
    purpose: str = ""
    triggers: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    playbook: str = ""
    raw_content: str = ""


class SkillsLibrary:
    """Manages filesystem-based skills."""

    def __init__(self, skills_dirs: Optional[List[Path]] = None):
        self.skills_dirs = skills_dirs or [REPO_SKILLS_DIR, DEFAULT_SKILLS_DIR]
        self._cache: Dict[str, Skill] = {}

    def list_skills(self) -> List[str]:
        """List all available skill names."""
        skills = set()
        for skills_dir in self.skills_dirs:
            if skills_dir.exists():
                for d in skills_dir.iterdir():
                    if d.is_dir() and (d / "SKILL.md").exists():
                        skills.add(d.name)
        return sorted(skills)

    def load_skill(self, name: str) -> Optional[Skill]:
        """Load a skill by name."""
        if name in self._cache:
            return self._cache[name]

        for skills_dir in self.skills_dirs:
            skill_dir = skills_dir / name
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skill = self._parse_skill(name, skill_dir, skill_file)
                self._cache[name] = skill
                return skill

        return None

    def load_all(self) -> Dict[str, Skill]:
        """Load all available skills."""
        for name in self.list_skills():
            self.load_skill(name)
        return dict(self._cache)

    def match_skill(self, query: str) -> List[str]:
        """Find skills that match a query based on triggers and purpose."""
        query_lower = query.lower()
        matches = []

        for name in self.list_skills():
            skill = self.load_skill(name)
            if not skill:
                continue

            score = 0
            # Check triggers
            for trigger in skill.triggers:
                if trigger.lower() in query_lower:
                    score += 10

            # Check purpose
            for word in query_lower.split():
                if word in skill.purpose.lower():
                    score += 1

            # Check name
            if name in query_lower:
                score += 5

            if score > 0:
                matches.append((name, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in matches]

    def get_skill_summary(self, name: str) -> Optional[Dict]:
        """Get a brief summary of a skill."""
        skill = self.load_skill(name)
        if not skill:
            return None
        return {
            "name": skill.name,
            "purpose": skill.purpose,
            "triggers": skill.triggers,
            "inputs": skill.inputs,
            "outputs": skill.outputs,
        }

    def _parse_skill(self, name: str, skill_dir: Path, skill_file: Path) -> Skill:
        """Parse a SKILL.md file into a Skill object."""
        content = skill_file.read_text(encoding="utf-8", errors="replace")

        skill = Skill(name=name, path=skill_dir, raw_content=content)

        # Parse sections
        sections = self._split_sections(content)

        skill.purpose = sections.get("purpose", sections.get("description", "")).strip()
        skill.triggers = self._parse_list(sections.get("triggers", ""))
        skill.inputs = self._parse_list(sections.get("inputs", sections.get("input", "")))
        skill.outputs = self._parse_list(sections.get("outputs", sections.get("output", "")))
        skill.playbook = sections.get("playbook", sections.get("steps", "")).strip()

        return skill

    def _split_sections(self, content: str) -> Dict[str, str]:
        """Split markdown content into sections by headers."""
        sections = {}
        current_section = "description"
        current_content = []

        for line in content.split("\n"):
            header_match = re.match(r"^#+\s+(.+)$", line)
            if header_match:
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = header_match.group(1).lower().strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _parse_list(self, text: str) -> List[str]:
        """Parse a markdown list into items."""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.")):
                item = re.sub(r"^[-*\d.]+\s*", "", line).strip()
                if item:
                    items.append(item)
        return items
