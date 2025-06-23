# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Misc. shared code."""

from typing import Final, NoReturn, final

__all__ = ["JSON", "Json", "JsonArray", "JsonBranch", "JsonLeaf", "JsonLimb", "JsonPrimitive"]

type JsonPrimitive = str | int | float | bool | None
type JsonArray = list[Json]
type JsonLeaf = JsonPrimitive | JsonArray
type JsonBranch = dict[str, Json]  # aka object
type JsonLimb = dict[str, JsonLeaf]
type Json = JsonLeaf | JsonBranch


@final
class _JsonUtil:
    """Trivial JSON serialization/deserialization wrapper."""

    def __str__(self) -> str:
        return "JSON"

    def __repr__(self) -> str:
        return "JSON"

    def encode(self, data: Json) -> str:
        import json  # noqa: PLC0415

        return json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2)

    def decode(self, data: str) -> Json:
        import json  # noqa: PLC0415

        return json.loads(data, parse_constant=self._parse_const)

    def _parse_const(self, s: str) -> NoReturn:
        msg = f"Invalid JSON value: '{s}'"
        raise ValueError(msg)


JSON: Final = _JsonUtil()
