# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Centralized registry of Tyranno template expression functions."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from typing import Any, Final

import yaml as _yaml_lib

from tyranno_sandbox._global_vars import STARTUP
from tyranno_sandbox.functions.pep440 import Pep440Dict, Pep440Functions
from tyranno_sandbox.functions.semver import SemverDict, SemverFunctions
from tyranno_sandbox.functions.times import DatetimeFunctions, TimeDict

__all__ = [
    "FUNCS",
    "SOURCE_FUNCS",
    "from_json",
    "from_yaml",
    "join",
    "lower",
    "now_local",
    "now_utc",
    "pep440",
    "pep440_minor",
    "replace",
    "semver",
    "sort",
    "timestamp",
    "upper",
    "yaml",
    "yaml_multiline",
]

# Maps name → callable(value: Any, *extra_args: str) → Any
FUNCS: Final[dict[str, Callable[..., Any]]] = {}

# Maps name → callable(*extra_args: str) → Any  (produces a value; ignores pipeline input)
SOURCE_FUNCS: Final[dict[str, Callable[..., Any]]] = {}

_f_time: Final = DatetimeFunctions()
_f_pep440: Final = Pep440Functions()
_f_semver: Final = SemverFunctions()


def _func(name: str) -> Callable[[Callable], Callable]:
    def decorator(fn: Callable) -> Callable:
        FUNCS[name] = fn
        return fn

    return decorator


def _source(name: str) -> Callable[[Callable], Callable]:
    def decorator(fn: Callable) -> Callable:
        SOURCE_FUNCS[name] = fn
        return fn

    return decorator


def _yaml_dump(value: Any) -> str:
    raw = _yaml_lib.dump(value, allow_unicode=True, default_flow_style=False)
    return raw.strip().removesuffix("...").strip()


# ── Source functions ──────────────────────────────────────────────────────────


@_source("now_utc")
def now_utc() -> TimeDict:
    return _f_time.of(STARTUP.utc)


@_source("now_local")
def now_local() -> TimeDict:
    return _f_time.of(STARTUP.local)


# ── Transform functions ───────────────────────────────────────────────────────


@_func("yaml")
def yaml(value: Any) -> str:
    return _yaml_dump(value)


@_func("from_yaml")
def from_yaml(value: Any) -> Any:
    return _yaml_lib.safe_load(str(value))


@_func("from_json")
def from_json(value: Any) -> Any:
    return json.loads(str(value))


@_func("yaml_multiline")
def yaml_multiline(value: Any, indent: int = 0) -> str:
    pad = " " * int(indent)
    items = value if isinstance(value, list) else [v.strip() for v in str(value).split(",") if v.strip()]
    return "\n".join(f"{pad}{_yaml_dump(item)}" for item in items)


@_func("lower")
def lower(value: Any) -> str:
    return str(value).lower()


@_func("upper")
def upper(value: Any) -> str:
    return str(value).upper()


@_func("replace")
def replace(value: Any, old: str, new: str) -> str:
    return str(value).replace(old, new)


@_func("pep440")
def pep440(value: Any) -> Pep440Dict:
    return _f_pep440.of(str(value))


@_func("pep440_minor")
def pep440_minor(value: Any) -> str:
    return _f_pep440.of(str(value))["minor_version"]


@_func("semver")
def semver(value: Any) -> SemverDict:
    return _f_semver.of(str(value))


@_func("timestamp")
def timestamp(value: Any) -> TimeDict:
    return _f_time.of(datetime.fromisoformat(str(value)))


@_func("sort")
def sort(value: Any) -> str:
    items = value if isinstance(value, list) else [i.strip() for i in str(value).split(",") if i.strip()]
    return ", ".join(str(v) for v in sorted(items, key=str))


@_func("join")
def join(value: Any, sep: str = ", ") -> str:
    items = value if isinstance(value, list) else [i.strip() for i in str(value).split(",")]
    return sep.join(str(i) for i in items)
