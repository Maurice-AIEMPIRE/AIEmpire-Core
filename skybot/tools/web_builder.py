"""
Web Builder Tool
================
Generates HTML/CSS/JS websites and saves them to the workspace.
Can create landing pages, sales pages, portfolios, etc.
"""

from pathlib import Path

from skybot.tools.base import BaseTool
from skybot.config import WORKSPACE_DIR


class WebBuilderTool(BaseTool):
    name = "web_builder"
    description = "Generate and save HTML/CSS/JS website files. Creates landing pages, sales pages, portfolios."

    def definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name for the website project (used as folder name).",
                    },
                    "html": {
                        "type": "string",
                        "description": "Complete HTML content for index.html.",
                    },
                    "css": {
                        "type": "string",
                        "description": "CSS styles (saved as style.css). Optional if styles are inline.",
                    },
                    "javascript": {
                        "type": "string",
                        "description": "JavaScript code (saved as script.js). Optional.",
                    },
                    "additional_files": {
                        "type": "object",
                        "description": "Additional files as {filename: content} pairs.",
                    },
                },
                "required": ["project_name", "html"],
            },
        }

    async def execute(
        self,
        project_name: str,
        html: str,
        css: str = "",
        javascript: str = "",
        additional_files: dict | None = None,
        **kwargs,
    ) -> str:
        # Sanitize project name
        safe_name = "".join(c for c in project_name if c.isalnum() or c in "-_").strip()
        if not safe_name:
            safe_name = "website"

        project_dir = WORKSPACE_DIR / "websites" / safe_name
        project_dir.mkdir(parents=True, exist_ok=True)

        files_created = []

        # Write index.html
        index_path = project_dir / "index.html"
        index_path.write_text(html, encoding="utf-8")
        files_created.append(f"index.html ({len(html)} chars)")

        # Write style.css
        if css:
            css_path = project_dir / "style.css"
            css_path.write_text(css, encoding="utf-8")
            files_created.append(f"style.css ({len(css)} chars)")

        # Write script.js
        if javascript:
            js_path = project_dir / "script.js"
            js_path.write_text(javascript, encoding="utf-8")
            files_created.append(f"script.js ({len(javascript)} chars)")

        # Write additional files
        if additional_files:
            for filename, content in additional_files.items():
                # Security: no path traversal
                safe_filename = Path(filename).name
                file_path = project_dir / safe_filename
                file_path.write_text(str(content), encoding="utf-8")
                files_created.append(f"{safe_filename} ({len(str(content))} chars)")

        result = (
            f"Website '{safe_name}' created!\n\n"
            f"Location: {project_dir.relative_to(WORKSPACE_DIR)}/\n\n"
            f"Files:\n"
        )
        for f in files_created:
            result += f"  - {f}\n"

        result += f"\nTo preview, open: {project_dir}/index.html"

        return result
