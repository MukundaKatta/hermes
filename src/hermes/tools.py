"""Tool registry for sub-agents.

A :class:`ToolBelt` holds a set of :class:`Tool` objects that agents can
discover by name or keyword search and invoke on demand.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    """A single invocable tool.

    Attributes:
        name: Unique tool name.
        description: What the tool does (used for search).
        handler: Callable that implements the tool logic.
        tags: Optional keyword tags to improve discoverability.
    """

    name: str
    description: str
    handler: Callable[..., Any]
    tags: List[str] = field(default_factory=list)

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool handler with given arguments."""
        return self.handler(*args, **kwargs)


class ToolBelt:
    """Registry of :class:`Tool` objects with search and invocation helpers.

    Example::

        belt = ToolBelt()
        belt.register(Tool(name="add", description="Add two numbers",
                           handler=lambda a, b: a + b))
        result = belt.invoke("add", 2, 3)
        assert result == 5
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Add a tool to the belt. Raises if name already taken."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """Remove a tool by name. Returns *True* if it existed."""
        return self._tools.pop(name, None) is not None

    def get(self, name: str) -> Optional[Tool]:
        """Look up a tool by exact name."""
        return self._tools.get(name)

    def search(self, query: str) -> List[Tool]:
        """Return tools whose name, description, or tags contain *query*."""
        query_lower = query.lower()
        matches: List[Tool] = []
        for tool in self._tools.values():
            haystack = " ".join([
                tool.name.lower(),
                tool.description.lower(),
                " ".join(t.lower() for t in tool.tags),
            ])
            if query_lower in haystack:
                matches.append(tool)
        return matches

    def invoke(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Look up *name* and call its handler. Raises KeyError if missing."""
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Unknown tool: '{name}'")
        return tool.invoke(*args, **kwargs)

    @property
    def tool_names(self) -> List[str]:
        return sorted(self._tools.keys())

    @property
    def count(self) -> int:
        return len(self._tools)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return a serialisable summary of all registered tools."""
        return [
            {"name": t.name, "description": t.description, "tags": t.tags}
            for t in self._tools.values()
        ]
