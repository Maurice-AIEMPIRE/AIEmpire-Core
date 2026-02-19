"""SkyBot Tools — Available tools for the AI agent."""

from skybot.tools.web_search import WebSearchTool
from skybot.tools.code_exec import CodeExecTool
from skybot.tools.file_ops import FileOpsTool
from skybot.tools.github_search import GitHubSearchTool
from skybot.tools.web_builder import WebBuilderTool

ALL_TOOLS = [
    WebSearchTool(),
    CodeExecTool(),
    FileOpsTool(),
    GitHubSearchTool(),
    WebBuilderTool(),
]

# Claude tool definitions (API format)
TOOL_DEFINITIONS = [t.definition() for t in ALL_TOOLS]

# Lookup by name
TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}

__all__ = [
    "ALL_TOOLS",
    "TOOL_DEFINITIONS",
    "TOOLS_BY_NAME",
    "WebSearchTool",
    "CodeExecTool",
    "FileOpsTool",
    "GitHubSearchTool",
    "WebBuilderTool",
]
