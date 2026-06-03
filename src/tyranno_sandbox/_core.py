# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Misc. shared code."""

from collections.abc import MutableMapping, MutableSequence
from typing import Final, NoReturn, final

try:
    import orjson as json
except ImportError:
    import json

__all__ = ["JSON", "Json", "JsonArray", "JsonBranch", "JsonLeaf", "JsonLimb", "JsonPrimitive"]

type JsonPrimitive = str | int | float | bool | None
type JsonArray = MutableSequence[Json]
type JsonLeaf = JsonPrimitive | JsonArray
type JsonBranch = MutableMapping[str, Json]  # aka object
type JsonLimb = MutableMapping[str, JsonLeaf]
type Json = JsonLeaf | JsonBranch

type YamlPrimitive = JsonPrimitive
type YamlArray = MutableSequence[Yaml]
type YamlLeaf = YamlPrimitive | YamlArray
type YamlBranch = MutableMapping[Yaml, Yaml]  # different from JSON
type Yaml = YamlLeaf | YamlBranch


@final
class _JsonUtil:
    """Trivial JSON serialization/deserialization wrapper."""

    def __str__(self) -> str:
        return "JSON"

    def __repr__(self) -> str:
        return "JSON"

    def encode(self, data: Json) -> str:
        return json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2)

    def decode(self, data: str) -> Json:
        import json  # noqa: PLC0415

        return json.loads(data, parse_constant=self._parse_const)

    @staticmethod
    def _parse_const(s: str) -> NoReturn:
        msg = f"Invalid JSON value: '{s}'"
        raise ValueError(msg)


JSON: Final = _JsonUtil()
