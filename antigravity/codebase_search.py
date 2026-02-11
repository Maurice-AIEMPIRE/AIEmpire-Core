"""
Codebase Search
================
Semantic + fuzzy search across the codebase.
Combines ripgrep (exact), fuzzy matching, and file outline parsing.

Inspired by Google Antigravity's codebase_search tool.

Usage:
    cs = CodebaseSearch()
    results = cs.search("API auth handler")
    results = cs.search_files("*.py", "antigravity/")
    outline = cs.file_outline("antigravity/unified_router.py")
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class SearchResult:
    """A single search result."""
    file: str
    line: int
    content: str
    score: float = 0.0
    context_before: list[str] = field(default_factory=list)
    context_after: list[str] = field(default_factory=list)


@dataclass
class FileOutline:
    """Outline of a file's structure."""
    file: str
    classes: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)


class CodebaseSearch:
    """
    Multi-strategy codebase search.

    Strategies:
    1. Exact grep (ripgrep if available, fallback to grep)
    2. Fuzzy matching (token-based scoring)
    3. File outline parsing (classes, functions, imports)
    """

    IGNORE_DIRS = {
        "__pycache__", ".git", "node_modules", ".venv", "venv",
        ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
        ".next", ".artifacts", "_artifacts",
    }

    IGNORE_FILES = {
        "*.pyc", "*.pyo", "*.so", "*.dll", "*.exe",
        "*.jpg", "*.png", "*.gif", "*.ico", "*.svg",
        "*.woff", "*.woff2", "*.ttf", "*.eot",
    }

    def __init__(self, root: Optional[Path] = None):
        self.root = root or PROJECT_ROOT
        self._has_ripgrep = self._check_ripgrep()

    def search(
        self,
        query: str,
        file_pattern: str = "*.py",
        max_results: int = 20,
        context_lines: int = 2,
    ) -> list[SearchResult]:
        """
        Search the codebase using multiple strategies.

        Args:
            query: Search query (text or regex)
            file_pattern: Glob pattern for files to search
            max_results: Maximum results to return
            context_lines: Lines of context around matches
        """
        results = []

        # Strategy 1: Exact grep
        grep_results = self._grep_search(query, file_pattern, context_lines)
        results.extend(grep_results)

        # Strategy 2: Fuzzy token matching (if grep found few results)
        if len(results) < max_results // 2:
            fuzzy_results = self._fuzzy_search(query, file_pattern)
            # Deduplicate
            seen = {(r.file, r.line) for r in results}
            for r in fuzzy_results:
                if (r.file, r.line) not in seen:
                    results.append(r)
                    seen.add((r.file, r.line))

        # Sort by score and limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_results]

    def search_in_file(
        self,
        filepath: str,
        query: str,
        context_lines: int = 3,
    ) -> list[SearchResult]:
        """Search within a specific file."""
        full_path = self.root / filepath
        if not full_path.exists():
            return []

        results = []
        lines = full_path.read_text().splitlines()
        query_lower = query.lower()

        for i, line in enumerate(lines):
            if query_lower in line.lower():
                ctx_before = lines[max(0, i - context_lines):i]
                ctx_after = lines[i + 1:i + 1 + context_lines]
                results.append(SearchResult(
                    file=filepath,
                    line=i + 1,
                    content=line.strip(),
                    score=1.0 if query in line else 0.8,
                    context_before=ctx_before,
                    context_after=ctx_after,
                ))

        return results

    def find_files(
        self,
        pattern: str,
        directory: str = "",
        max_results: int = 50,
    ) -> list[str]:
        """Find files by name pattern (like fd/find)."""
        search_root = self.root / directory if directory else self.root
        matches = []

        for path in search_root.rglob(pattern):
            if any(ignore in path.parts for ignore in self.IGNORE_DIRS):
                continue
            rel = str(path.relative_to(self.root))
            matches.append(rel)
            if len(matches) >= max_results:
                break

        return sorted(matches)

    def file_outline(self, filepath: str) -> FileOutline:
        """
        Get the structural outline of a Python file.
        Returns classes, functions, imports, and constants.
        """
        full_path = self.root / filepath
        if not full_path.exists():
            return FileOutline(file=filepath)

        content = full_path.read_text()
        lines = content.splitlines()
        outline = FileOutline(file=filepath)

        current_class = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Imports
            if stripped.startswith(("import ", "from ")):
                outline.imports.append(stripped)

            # Classes
            class_match = re.match(r"^class\s+(\w+)(?:\(([^)]*)\))?:", stripped)
            if class_match:
                current_class = class_match.group(1)
                bases = class_match.group(2) or ""
                outline.classes.append({
                    "name": current_class,
                    "line": i + 1,
                    "bases": bases,
                    "methods": [],
                })

            # Functions/methods
            func_match = re.match(r"^(\s*)(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)", line)
            if func_match:
                indent = len(func_match.group(1))
                func_name = func_match.group(2)
                params = func_match.group(3)

                func_info = {
                    "name": func_name,
                    "line": i + 1,
                    "params": params.strip(),
                    "async": "async def" in line,
                }

                if indent > 0 and current_class and outline.classes:
                    outline.classes[-1]["methods"].append(func_info)
                else:
                    outline.functions.append(func_info)
                    current_class = None

            # Module-level constants (UPPER_CASE = ...)
            const_match = re.match(r"^([A-Z][A-Z0-9_]+)\s*=", stripped)
            if const_match and not stripped.startswith("class "):
                outline.constants.append(f"{const_match.group(1)} (line {i + 1})")

        return outline

    def _grep_search(
        self,
        query: str,
        file_pattern: str,
        context_lines: int,
    ) -> list[SearchResult]:
        """Search using ripgrep or grep."""
        results = []

        try:
            if self._has_ripgrep:
                cmd = [
                    "rg", "--json",
                    "-g", file_pattern,
                    "-C", str(context_lines),
                    "--max-count", "50",
                    "-i",
                    query,
                    str(self.root),
                ]
            else:
                cmd = [
                    "grep", "-rn", "-i",
                    "--include", file_pattern,
                    "-C", str(context_lines),
                    query,
                    str(self.root),
                ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )

            if self._has_ripgrep:
                results = self._parse_rg_json(result.stdout)
            else:
                results = self._parse_grep_output(result.stdout)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return results

    def _fuzzy_search(
        self,
        query: str,
        file_pattern: str,
    ) -> list[SearchResult]:
        """Fuzzy token-based search."""
        results = []
        query_tokens = set(query.lower().split())

        for filepath in self.root.rglob(file_pattern):
            if any(ignore in filepath.parts for ignore in self.IGNORE_DIRS):
                continue

            try:
                content = filepath.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            for i, line in enumerate(content.splitlines()):
                line_lower = line.lower()
                line_tokens = set(re.findall(r"\w+", line_lower))

                # Calculate token overlap score
                overlap = query_tokens & line_tokens
                if len(overlap) >= max(1, len(query_tokens) // 2):
                    score = len(overlap) / len(query_tokens)
                    rel_path = str(filepath.relative_to(self.root))
                    results.append(SearchResult(
                        file=rel_path,
                        line=i + 1,
                        content=line.strip(),
                        score=score * 0.7,  # Fuzzy results score lower
                    ))

        return results

    def _parse_rg_json(self, output: str) -> list[SearchResult]:
        """Parse ripgrep JSON output."""
        import json
        results = []
        for line in output.splitlines():
            try:
                data = json.loads(line)
                if data.get("type") == "match":
                    match_data = data["data"]
                    path = match_data.get("path", {}).get("text", "")
                    try:
                        rel_path = str(Path(path).relative_to(self.root))
                    except ValueError:
                        rel_path = path
                    line_num = match_data.get("line_number", 0)
                    text = match_data.get("lines", {}).get("text", "").strip()
                    results.append(SearchResult(
                        file=rel_path,
                        line=line_num,
                        content=text,
                        score=1.0,
                    ))
            except (json.JSONDecodeError, KeyError):
                continue
        return results

    def _parse_grep_output(self, output: str) -> list[SearchResult]:
        """Parse standard grep output."""
        results = []
        for line in output.splitlines():
            match = re.match(r"^(.+?):(\d+):(.*)$", line)
            if match:
                filepath = match.group(1)
                try:
                    rel_path = str(Path(filepath).relative_to(self.root))
                except ValueError:
                    rel_path = filepath
                results.append(SearchResult(
                    file=rel_path,
                    line=int(match.group(2)),
                    content=match.group(3).strip(),
                    score=1.0,
                ))
        return results

    def _check_ripgrep(self) -> bool:
        """Check if ripgrep is available."""
        try:
            subprocess.run(["rg", "--version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def status_report(self) -> str:
        """Get codebase search status."""
        py_files = len(self.find_files("*.py"))
        js_files = len(self.find_files("*.js"))
        json_files = len(self.find_files("*.json"))
        md_files = len(self.find_files("*.md"))

        return (
            f"Codebase Search Status\n"
            f"  Root: {self.root}\n"
            f"  Backend: {'ripgrep' if self._has_ripgrep else 'grep'}\n"
            f"  Python files: {py_files}\n"
            f"  JS files: {js_files}\n"
            f"  JSON files: {json_files}\n"
            f"  Markdown files: {md_files}"
        )
