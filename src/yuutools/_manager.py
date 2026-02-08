"""ToolManager — typed registry for tools."""

from __future__ import annotations

from typing import Generic, TypeVar

import attrs

from yuutools._tool import Tool

Ctx = TypeVar("Ctx")


@attrs.define(slots=True, init=False)
class ToolManager(Generic[Ctx]):
    """A simple name-keyed registry of :class:`Tool` objects.

    Usage::

        manager = ToolManager[MyCtx]([tool_a, tool_b])
        t = manager["tool_a"]
    """

    _tools: dict[str, Tool[Ctx]] = attrs.field(factory=dict, repr=False)

    def __init__(self, tools: list[Tool[Ctx]] | None = None) -> None:
        self._tools = {}
        for t in tools or []:
            self.register(t)

    def register(self, t: Tool[Ctx]) -> None:
        """Add a tool to the registry.  Raises on duplicate names."""
        if t.spec.name in self._tools:
            raise ValueError(f"duplicate tool name: {t.spec.name!r}")
        self._tools[t.spec.name] = t

    def __getitem__(self, name: str) -> Tool[Ctx]:
        try:
            return self._tools[name]
        except KeyError:
            raise KeyError(
                f"no tool named {name!r}; "
                f"available: {list(self._tools)}"
            ) from None

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __iter__(self):
        return iter(self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)

    @property
    def names(self) -> list[str]:
        return list(self._tools)

    def specs(self) -> list[dict]:
        """Return JSON-schema-ready specs for all tools (for LLM function calling)."""
        import json
        return [json.loads(t.spec.to("json_schema")) for t in self._tools.values()]
