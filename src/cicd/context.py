# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Wrapper around repo for Tyrannosaurus.
"""

import glob
import re
import tomllib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePath
from typing import Self
from collections.abc import Iterator

import jmespath

from ._global_vars import GlobalVars
from cicd.dot_tree import Toml, DotTree

__all__ = ["Context", "ContextFactory", "Data", "DefaultContextFactory"]
_PATTERN = re.compile(r"\$\{ *([-._A-Za-z0-9]*) *(?:~ *([^~]+) *~ *)?}")
_TYRANNO = ":tyranno:"
_SUBSTITUTION_PATTERN = re.compile(r"\${([^}]+)}")


@dataclass(frozen=True, slots=True)
class Data:
    """"""

    data: DotTree

    def get(self: Self, key: str) -> Toml | None:
        try:
            return self._sub(key, None)
        except KeyError:
            return None

    def req(self: Self, key: str) -> Toml:
        return self._sub(key, None)

    def _sub(self: Self, key: str, james: str | None) -> Toml:
        key = "tool.tyranno.data" if key == "." else "tool.tyranno.data" + key
        result = self.data.demand(key)
        return jmespath.search(james, result) if james else result

    def _get_value(self, key: str):
        # TODO: what is this for?
        value = self.data
        match value:
            case list():
                result = [self._sub(v, None) for v in value]
            case dict():
                result = {k: self._sub(v, None) for k, v in value.items()}
            case str():
                result = _PATTERN.sub(lambda p: self._sub(p.group(1), p.group(2)), value)
            case int() | float() | datetime() | date():
                result = value
            case _:
                raise AssertionError(f"Impossible type {value}")
        return result


@dataclass(frozen=True, slots=True, kw_only=True)
class Context:
    """"""

    repo_dir: Path
    config: Data
    dry_run: bool
    global_vars: GlobalVars

    @property
    def data(self: Self) -> Data:
        return Data(self.config.data.demand_subtree("tool.tyranno.data"))

    @property
    def trash_dir(self: Self) -> Path:
        return self.repo_path / self.trash_dir_name

    def find_targets(self: Self) -> Iterator[Path]:
        include = self.config.data.demand_subtree("tool.tyranno.target-globs")
        for pattern in include:
            for p in glob.glob(pattern):
                yield self.resolve_path(p)

    def find_trash(self: Self) -> Iterator[Path]:
        include = self.config.data.demand_subtree("tool.tyranno.trash-globs")
        for pattern in include:
            for p in glob.glob(pattern):
                yield self.resolve_path(p)

    def resolve_path(self: Self, path: PurePath | str) -> Path:
        path = Path(path).resolve(strict=True)
        if not str(path).startswith(str(self.repo_path)):
            raise AssertionError(f"{path} is not a descendent of {self.repo_path}")
        return path.relative_to(self.repo_path)


@dataclass(frozen=True, slots=True)
class ContextFactory:
    def __call__(self: Self, cwd: Path, global_vars: GlobalVars, *, dry_run: bool) -> Context:
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class DefaultContextFactory(ContextFactory):
    def __call__(self: Self, cwd: Path, global_vars: GlobalVars, *, dry_run: bool) -> Context:
        read = Path("pyproject.toml").read_text(encoding="utf-8")
        tree = DotTree.from_nested(tomllib.loads(read))
        return Context(
            repo_dir=cwd,
            config=Data(tree),
            dry_run=dry_run,
            global_vars=global_vars,
        )
