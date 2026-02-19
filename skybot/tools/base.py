"""Base class for all SkyBot tools."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class that all SkyBot tools inherit from."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def definition(self) -> dict:
        """Return Claude API tool definition."""

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool and return a string result."""

    def _truncate(self, text: str, max_len: int = 8000) -> str:
        """Truncate output if too long."""
        if len(text) <= max_len:
            return text
        half = max_len // 2 - 50
        return text[:half] + "\n\n... [truncated] ...\n\n" + text[-half:]
