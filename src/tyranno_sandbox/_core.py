# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Misc. shared code."""

from collections.abc import MutableMapping, MutableSequence
from typing import Final, NoReturn, final

import orjson

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
        return orjson.dumps(data, option=orjson.OPT_INDENT_2).decode()

    def decode(self, data: str) -> Json:
        return orjson.loads(data)


JSON: Final = _JsonUtil()
