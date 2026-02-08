"""Tests for yuutools core functionality."""

from __future__ import annotations

import json
import pytest
import yuutools as yt


# -- fixtures / helpers -----------------------------------------------------

class Ctx:
    """Minimal test context."""
    def __init__(self, multiplier: int = 10):
        self.multiplier = multiplier


def get_z(ctx: Ctx) -> int:
    return ctx.multiplier


@yt.tool(
    params={"x": "first operand", "y": "list of ints to sum"},
    name="goodtool",
    description="Add x + sum(y) + z",
)
async def goodtool(x: int, y: list[int], z: int = yt.depends(get_z)):
    return x + sum(y) + z


@yt.tool(params={"a": "a string"})
async def echo(a: str) -> str:
    return a


@yt.tool(params={"n": "number"})
def sync_tool(n: int) -> int:
    """A sync tool."""
    return n * 2


# -- tests ------------------------------------------------------------------


class TestDepends:
    def test_returns_marker(self):
        marker = yt.depends.__wrapped__(get_z) if hasattr(yt.depends, "__wrapped__") else yt.DependencyMarker(get_z)
        assert isinstance(marker, yt.DependencyMarker)
        assert marker.resolver is get_z

    def test_marker_repr(self):
        marker = yt.DependencyMarker(get_z)
        assert "DependencyMarker" in repr(marker)


class TestToolDecorator:
    def test_returns_tool_instance(self):
        assert isinstance(goodtool, yt.Tool)

    def test_spec_name(self):
        assert goodtool.spec.name == "goodtool"

    def test_spec_description(self):
        assert goodtool.spec.description == "Add x + sum(y) + z"

    def test_dep_params_hidden_from_spec(self):
        names = [p.name for p in goodtool.spec.params]
        assert "z" not in names
        assert "x" in names
        assert "y" in names

    def test_param_descriptions(self):
        by_name = {p.name: p for p in goodtool.spec.params}
        assert by_name["x"].description == "first operand"
        assert by_name["y"].description == "list of ints to sum"

    def test_default_name_from_function(self):
        assert echo.spec.name == "echo"

    def test_sync_tool_docstring_fallback(self):
        assert sync_tool.spec.description == "A sync tool."


class TestToolSpec:
    def test_to_json_schema(self):
        raw = goodtool.spec.to("json_schema")
        schema = json.loads(raw)
        assert schema["type"] == "function"
        fn = schema["function"]
        assert fn["name"] == "goodtool"
        props = fn["parameters"]["properties"]
        assert props["x"]["type"] == "integer"
        assert props["y"]["type"] == "array"
        assert props["y"]["items"]["type"] == "integer"
        assert "z" not in props
        assert "x" in fn["parameters"]["required"]

    def test_to_yaml(self):
        raw = goodtool.spec.to("yaml")
        assert "goodtool" in raw
        assert "integer" in raw

    def test_to_invalid_format(self):
        with pytest.raises(ValueError, match="unsupported format"):
            goodtool.spec.to("xml")


class TestBoundTool:
    @pytest.mark.asyncio
    async def test_run_with_positional(self):
        ctx = Ctx(multiplier=100)
        result = await goodtool.bind(ctx).run(1, [2, 3])
        assert result == 1 + 5 + 100

    @pytest.mark.asyncio
    async def test_run_with_kwargs(self):
        ctx = Ctx(multiplier=7)
        result = await goodtool.bind(ctx).run(x=2, y=[10])
        assert result == 2 + 10 + 7

    @pytest.mark.asyncio
    async def test_run_kwargs_from_dict(self):
        ctx = Ctx(multiplier=0)
        arguments = {"x": 5, "y": [1, 2, 3]}
        result = await goodtool.bind(ctx).run(**arguments)
        assert result == 5 + 6 + 0

    @pytest.mark.asyncio
    async def test_sync_tool_works(self):
        ctx = Ctx()
        result = await sync_tool.bind(ctx).run(3)
        assert result == 6


class TestToolManager:
    def test_register_and_lookup(self):
        mgr = yt.ToolManager([goodtool, echo])
        assert mgr["goodtool"] is goodtool
        assert mgr["echo"] is echo

    def test_missing_key(self):
        mgr = yt.ToolManager([goodtool])
        with pytest.raises(KeyError, match="no tool named"):
            mgr["nonexistent"]

    def test_duplicate_raises(self):
        with pytest.raises(ValueError, match="duplicate"):
            yt.ToolManager([goodtool, goodtool])

    def test_contains(self):
        mgr = yt.ToolManager([goodtool])
        assert "goodtool" in mgr
        assert "nope" not in mgr

    def test_len_and_iter(self):
        mgr = yt.ToolManager([goodtool, echo])
        assert len(mgr) == 2
        assert set(mgr.names) == {"goodtool", "echo"}

    def test_specs(self):
        mgr = yt.ToolManager([goodtool])
        specs = mgr.specs()
        assert len(specs) == 1
        assert specs[0]["function"]["name"] == "goodtool"
