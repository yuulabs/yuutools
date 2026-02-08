"""Tests for the type -> JSON Schema conversion."""

from __future__ import annotations

import typing
from typing import Literal, Optional, Union

from yuutools._schema import type_to_json_schema


class TestPrimitives:
    def test_int(self):
        assert type_to_json_schema(int) == {"type": "integer"}

    def test_float(self):
        assert type_to_json_schema(float) == {"type": "number"}

    def test_str(self):
        assert type_to_json_schema(str) == {"type": "string"}

    def test_bool(self):
        assert type_to_json_schema(bool) == {"type": "boolean"}


class TestContainers:
    def test_list_int(self):
        assert type_to_json_schema(list[int]) == {
            "type": "array",
            "items": {"type": "integer"},
        }

    def test_dict_str_int(self):
        assert type_to_json_schema(dict[str, int]) == {
            "type": "object",
            "additionalProperties": {"type": "integer"},
        }

    def test_tuple(self):
        schema = type_to_json_schema(tuple[int, str])
        assert schema["type"] == "array"
        assert len(schema["prefixItems"]) == 2


class TestOptionalAndUnion:
    def test_optional(self):
        schema = type_to_json_schema(Optional[int])
        assert schema == {"anyOf": [{"type": "integer"}, {"type": "null"}]}

    def test_union(self):
        schema = type_to_json_schema(Union[int, str])
        assert schema == {
            "anyOf": [{"type": "integer"}, {"type": "string"}]
        }

    def test_pipe_union(self):
        schema = type_to_json_schema(int | str)
        assert schema == {
            "anyOf": [{"type": "integer"}, {"type": "string"}]
        }


class TestLiteral:
    def test_literal(self):
        schema = type_to_json_schema(Literal["a", "b"])
        assert schema == {"enum": ["a", "b"]}


class TestNested:
    def test_list_of_list(self):
        schema = type_to_json_schema(list[list[int]])
        assert schema == {
            "type": "array",
            "items": {"type": "array", "items": {"type": "integer"}},
        }
