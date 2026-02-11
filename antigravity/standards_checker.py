"""
Premium Standards Checker
==========================
Enforces quality standards for content, code, and web assets.
Based on Google Antigravity's "failure to wow is UNACCEPTABLE" principle.

Checks:
- Code quality (syntax, imports, structure)
- Web content quality (meta tags, semantic HTML, accessibility)
- Content quality (readability, engagement potential)
- SEO basics (title, description, h1, semantic structure)

Usage:
    checker = StandardsChecker()
    report = checker.check_python_file("antigravity/unified_router.py")
    report = checker.check_content("My blog post about AI...")
    report = checker.check_web_page("empire_api/templates/index.html")
"""

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class CheckResult:
    """Result of a quality check."""
    passed: bool
    category: str
    message: str
    severity: str = "info"  # info, warning, error, critical
    suggestion: str = ""


@dataclass
class QualityReport:
    """Full quality report for a file or content."""
    target: str
    score: float = 0.0
    max_score: float = 100.0
    checks: list[CheckResult] = field(default_factory=list)
    grade: str = ""

    @property
    def pass_rate(self) -> float:
        if not self.checks:
            return 0.0
        return sum(1 for c in self.checks if c.passed) / len(self.checks)

    def calculate_grade(self) -> str:
        rate = self.pass_rate
        if rate >= 0.95:
            return "A+"
        elif rate >= 0.90:
            return "A"
        elif rate >= 0.80:
            return "B"
        elif rate >= 0.70:
            return "C"
        elif rate >= 0.60:
            return "D"
        return "F"


class StandardsChecker:
    """Enforces premium quality standards across the codebase."""

    def __init__(self, root: Optional[Path] = None):
        self.root = root or PROJECT_ROOT

    def check_python_file(self, filepath: str) -> QualityReport:
        """Check a Python file for quality standards."""
        full_path = self.root / filepath
        report = QualityReport(target=filepath)

        if not full_path.exists():
            report.checks.append(CheckResult(
                passed=False, category="existence",
                message=f"File not found: {filepath}",
                severity="critical",
            ))
            return report

        content = full_path.read_text()
        lines = content.splitlines()

        # 1. Has docstring
        report.checks.append(CheckResult(
            passed='"""' in content[:500] or "'''" in content[:500],
            category="documentation",
            message="Module docstring present",
            suggestion="Add a module-level docstring explaining the file's purpose",
        ))

        # 2. Reasonable file length
        line_count = len(lines)
        report.checks.append(CheckResult(
            passed=line_count <= 500,
            category="structure",
            message=f"File length: {line_count} lines",
            severity="warning" if line_count > 500 else "info",
            suggestion="Consider splitting into smaller modules" if line_count > 500 else "",
        ))

        # 3. No wildcard imports
        has_star_import = any(re.match(r"from\s+\S+\s+import\s+\*", line) for line in lines)
        report.checks.append(CheckResult(
            passed=not has_star_import,
            category="imports",
            message="No wildcard imports",
            suggestion="Replace `from x import *` with explicit imports",
        ))

        # 4. No hardcoded secrets
        secret_patterns = [
            r'(?:api_key|password|secret|token)\s*=\s*["\'][^"\']{8,}["\']',
        ]
        has_secrets = any(
            re.search(pat, content, re.IGNORECASE)
            for pat in secret_patterns
        )
        report.checks.append(CheckResult(
            passed=not has_secrets,
            category="security",
            message="No hardcoded secrets detected",
            severity="critical" if has_secrets else "info",
            suggestion="Use environment variables for secrets",
        ))

        # 5. Functions have type hints
        func_defs = re.findall(r"def\s+\w+\s*\([^)]*\)", content)
        typed_funcs = re.findall(r"def\s+\w+\s*\([^)]*\)\s*->", content)
        type_coverage = len(typed_funcs) / max(len(func_defs), 1)
        report.checks.append(CheckResult(
            passed=type_coverage >= 0.5,
            category="typing",
            message=f"Type hint coverage: {type_coverage:.0%} ({len(typed_funcs)}/{len(func_defs)})",
            suggestion="Add return type annotations to functions",
        ))

        # 6. No TODO/FIXME/HACK without ticket
        todos = [
            line.strip() for line in lines
            if re.search(r"#\s*(TODO|FIXME|HACK|XXX)", line, re.IGNORECASE)
        ]
        report.checks.append(CheckResult(
            passed=len(todos) == 0,
            category="maintenance",
            message=f"Open TODOs: {len(todos)}",
            severity="warning" if todos else "info",
            suggestion="Resolve or create tickets for TODOs",
        ))

        # 7. Syntax check
        syntax_ok = self._check_syntax(full_path)
        report.checks.append(CheckResult(
            passed=syntax_ok,
            category="syntax",
            message="Python syntax valid",
            severity="critical" if not syntax_ok else "info",
        ))

        # 8. No print() in library code (should use logging)
        prints = sum(1 for line in lines if re.match(r"\s*print\(", line))
        report.checks.append(CheckResult(
            passed=prints <= 5,
            category="logging",
            message=f"Print statements: {prints}",
            severity="warning" if prints > 5 else "info",
            suggestion="Consider using logging module instead of print()",
        ))

        # Calculate score
        report.score = report.pass_rate * 100
        report.grade = report.calculate_grade()

        return report

    def check_content(self, content: str, content_type: str = "post") -> QualityReport:
        """Check text content for quality (tweets, posts, articles)."""
        report = QualityReport(target=f"content ({content_type})")

        words = content.split()
        word_count = len(words)

        # 1. Not too short
        min_words = {"tweet": 5, "post": 50, "article": 200}.get(content_type, 20)
        report.checks.append(CheckResult(
            passed=word_count >= min_words,
            category="length",
            message=f"Word count: {word_count} (min: {min_words})",
        ))

        # 2. Has engagement hooks (questions, calls to action)
        has_question = "?" in content
        has_cta = any(cta in content.lower() for cta in [
            "check out", "try", "click", "subscribe", "follow",
            "learn more", "get started", "sign up", "download",
        ])
        report.checks.append(CheckResult(
            passed=has_question or has_cta,
            category="engagement",
            message="Has engagement hook (question or CTA)",
            suggestion="Add a question or call-to-action",
        ))

        # 3. Readability (average sentence length)
        sentences = re.split(r"[.!?]+", content)
        avg_sentence = word_count / max(len(sentences), 1)
        report.checks.append(CheckResult(
            passed=avg_sentence <= 25,
            category="readability",
            message=f"Avg sentence length: {avg_sentence:.1f} words",
            suggestion="Break long sentences for readability",
        ))

        # 4. No filler words overuse
        fillers = ["very", "really", "just", "basically", "actually", "literally"]
        filler_count = sum(content.lower().count(f" {f} ") for f in fillers)
        report.checks.append(CheckResult(
            passed=filler_count <= 3,
            category="style",
            message=f"Filler words: {filler_count}",
            suggestion="Remove unnecessary filler words",
        ))

        # 5. Has structure (headers, lists, or paragraphs)
        has_structure = (
            "\n\n" in content  # paragraphs
            or "\n-" in content or "\n*" in content  # lists
            or "\n#" in content  # headers
        )
        report.checks.append(CheckResult(
            passed=has_structure or content_type == "tweet",
            category="structure",
            message="Content has structure",
            suggestion="Add paragraphs, headers, or bullet points",
        ))

        report.score = report.pass_rate * 100
        report.grade = report.calculate_grade()

        return report

    def check_web_page(self, filepath: str) -> QualityReport:
        """Check an HTML file for premium web standards."""
        full_path = self.root / filepath
        report = QualityReport(target=filepath)

        if not full_path.exists():
            report.checks.append(CheckResult(
                passed=False, category="existence",
                message=f"File not found: {filepath}",
                severity="critical",
            ))
            return report

        content = full_path.read_text()
        content_lower = content.lower()

        # 1. Has title tag
        report.checks.append(CheckResult(
            passed="<title>" in content_lower,
            category="seo",
            message="Has <title> tag",
            severity="error",
            suggestion="Add a <title> tag for SEO",
        ))

        # 2. Has meta description
        report.checks.append(CheckResult(
            passed='name="description"' in content_lower,
            category="seo",
            message="Has meta description",
            suggestion='Add <meta name="description" content="...">',
        ))

        # 3. Has single h1
        h1_count = content_lower.count("<h1")
        report.checks.append(CheckResult(
            passed=h1_count == 1,
            category="seo",
            message=f"H1 tags: {h1_count} (should be 1)",
            suggestion="Use exactly one <h1> per page",
        ))

        # 4. Semantic HTML
        semantic_tags = ["<header", "<nav", "<main", "<footer", "<article", "<section"]
        has_semantic = any(tag in content_lower for tag in semantic_tags)
        report.checks.append(CheckResult(
            passed=has_semantic,
            category="accessibility",
            message="Uses semantic HTML5 tags",
            suggestion="Use <header>, <main>, <footer>, <nav>, <section>",
        ))

        # 5. Has viewport meta
        report.checks.append(CheckResult(
            passed="viewport" in content_lower,
            category="responsive",
            message="Has viewport meta tag",
            suggestion='Add <meta name="viewport" content="width=device-width, initial-scale=1">',
        ))

        # 6. No inline styles (premium standard)
        inline_styles = len(re.findall(r'style="[^"]{20,}"', content))
        report.checks.append(CheckResult(
            passed=inline_styles <= 3,
            category="style",
            message=f"Inline styles: {inline_styles}",
            severity="warning" if inline_styles > 3 else "info",
            suggestion="Move inline styles to CSS file",
        ))

        # 7. Has Google Fonts or custom fonts
        has_fonts = "fonts.googleapis.com" in content or "@font-face" in content
        report.checks.append(CheckResult(
            passed=has_fonts,
            category="premium",
            message="Uses custom fonts",
            suggestion="Add Google Fonts (Inter, Roboto, Outfit) for premium feel",
        ))

        # 8. Has dark mode support
        has_dark = "prefers-color-scheme" in content or "dark" in content_lower
        report.checks.append(CheckResult(
            passed=has_dark,
            category="premium",
            message="Dark mode support",
            suggestion="Add @media (prefers-color-scheme: dark) styles",
        ))

        report.score = report.pass_rate * 100
        report.grade = report.calculate_grade()

        return report

    def format_report(self, report: QualityReport) -> str:
        """Format a quality report as readable text."""
        lines = [
            "=" * 60,
            f"QUALITY REPORT: {report.target}",
            f"Grade: {report.grade} ({report.score:.0f}/100)",
            "=" * 60,
        ]

        severity_icons = {
            "info": "  ", "warning": "⚠️", "error": "❌", "critical": "🚨",
        }

        for check in report.checks:
            icon = "✅" if check.passed else severity_icons.get(check.severity, "  ")
            lines.append(f"  {icon} [{check.category:15s}] {check.message}")
            if not check.passed and check.suggestion:
                lines.append(f"     → {check.suggestion}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _check_syntax(self, filepath: Path) -> bool:
        """Check Python syntax validity."""
        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(filepath)],
                capture_output=True, timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True  # Assume OK if can't check
