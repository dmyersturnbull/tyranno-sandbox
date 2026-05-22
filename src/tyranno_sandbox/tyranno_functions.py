# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Centralized registry of Tyranno template expression functions."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Final

import yaml
from packaging.version import Version

from tyranno_sandbox._global_vars import STARTUP

__all__ = ["FUNCS", "SOURCE_FUNCS"]

# Maps name → callable(value: Any, *extra_args: str) → Any
FUNCS: Final[dict[str, Callable[..., Any]]] = {}

# Maps name → callable(*extra_args: str) → Any  (produces a value; ignores pipeline input)
SOURCE_FUNCS: Final[dict[str, Callable[..., Any]]] = {}


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
    """Serialize *value* with PyYAML, stripping document-end markers."""
    raw = yaml.dump(value, allow_unicode=True, default_flow_style=False)
    return raw.strip().removesuffix("...").strip()


# ── Source functions ──────────────────────────────────────────────────────────


@_source("now_utc")
def _now_utc() -> object:
    return STARTUP.utc


@_source("now_local")
def _now_local() -> object:
    return STARTUP.local


# ── Transform functions ───────────────────────────────────────────────────────


@_func("yaml")
def _yaml_func(value: Any) -> str:
    return _yaml_dump(value)


@_func("from_yaml")
def _from_yaml(value: Any) -> Any:
    return yaml.safe_load(str(value))


@_func("from_json")
def _from_json(value: Any) -> Any:
    return json.loads(str(value))


@_func("yaml_multiline")
def _yaml_multiline(value: Any, indent: str = "0") -> str:
    pad = " " * int(indent)
    items = [v.strip() for v in str(value).split(",") if v.strip()]
    return "\n".join(f"{pad}{_yaml_dump(item)}" for item in items)


@_func("lower")
def _lower(value: Any) -> str:
    return str(value).lower()


@_func("upper")
def _upper(value: Any) -> str:
    return str(value).upper()


@_func("replace")
def _replace(value: Any, old: str, new: str) -> str:
    return str(value).replace(old, new)


@_func("spdx_license")
def _spdx_license(value: Any) -> str:
    return str(value)


@_func("pep440_minor")
def _pep440_minor(value: Any) -> str:
    v = Version(str(value))
    return f"{v.major}.{v.minor}"


@_func("sort")
def _sort(value: Any) -> str:
    items = [i.strip() for i in str(value).split(",")]
    return ", ".join(sorted(items))


@_func("join")
def _join(value: Any, sep: str = ", ") -> str:
    items = [i.strip() for i in str(value).split(",")]
    return sep.join(items)
