"""Tests for hermes.tools — Tool and ToolBelt."""
from __future__ import annotations

import pytest

from hermes.tools import Tool, ToolBelt


class TestTool:
    def test_invoke(self) -> None:
        t = Tool(name="add", description="add", handler=lambda a, b: a + b)
        assert t.invoke(2, 3) == 5

    def test_tags_default_empty(self) -> None:
        t = Tool(name="x", description="x", handler=lambda: None)
        assert t.tags == []


class TestToolBelt:
    def _belt_with_tools(self) -> ToolBelt:
        belt = ToolBelt()
        belt.register(Tool("add", "Add numbers", lambda a, b: a + b, tags=["math"]))
        belt.register(Tool("upper", "Uppercase text", str.upper, tags=["text"]))
        return belt

    def test_register_and_count(self) -> None:
        belt = self._belt_with_tools()
        assert belt.count == 2

    def test_duplicate_register_raises(self) -> None:
        belt = self._belt_with_tools()
        with pytest.raises(ValueError, match="already registered"):
            belt.register(Tool("add", "dup", lambda: None))

    def test_get(self) -> None:
        belt = self._belt_with_tools()
        assert belt.get("add") is not None
        assert belt.get("nonexistent") is None

    def test_invoke(self) -> None:
        belt = self._belt_with_tools()
        assert belt.invoke("add", 10, 20) == 30

    def test_invoke_missing_raises(self) -> None:
        belt = ToolBelt()
        with pytest.raises(KeyError, match="Unknown tool"):
            belt.invoke("nope")

    def test_search_by_name(self) -> None:
        belt = self._belt_with_tools()
        results = belt.search("add")
        assert len(results) == 1
        assert results[0].name == "add"

    def test_search_by_tag(self) -> None:
        belt = self._belt_with_tools()
        results = belt.search("math")
        assert len(results) == 1

    def test_search_by_description(self) -> None:
        belt = self._belt_with_tools()
        results = belt.search("Uppercase")
        assert len(results) == 1

    def test_unregister(self) -> None:
        belt = self._belt_with_tools()
        assert belt.unregister("add")
        assert belt.count == 1
        assert not belt.unregister("add")

    def test_tool_names_sorted(self) -> None:
        belt = self._belt_with_tools()
        assert belt.tool_names == ["add", "upper"]

    def test_list_tools(self) -> None:
        belt = self._belt_with_tools()
        listing = belt.list_tools()
        assert len(listing) == 2
        names = {t["name"] for t in listing}
        assert names == {"add", "upper"}
