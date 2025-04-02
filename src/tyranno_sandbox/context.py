# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Wrapper around repo for Tyrannosaurus.
"""

import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import jmespath
from pathspec import GitIgnoreSpec

from tyranno_sandbox.dot_tree import DotTree, Toml

__all__ = ["Context", "ContextFactory", "Data", "DefaultContextFactory"]


@dataclass(frozen=True, slots=True)
class Data:
    """"""

    tree: DotTree

    def get(self, key: str) -> Toml | None:
        try:
            return self._sub(key, None)
        except KeyError:
            return None

    def req(self, key: str) -> Toml:
        return self._sub(key, None)

    def _sub(self, key: str, james: str | None) -> Toml:
        key = "tool.tyranno.data" if key == "." else "tool.tyranno.data" + key
        result = self.tree.demand(key)
        return jmespath.search(james, result) if james else result


@dataclass(frozen=True, slots=True, kw_only=True)
class Context:
    """"""

    repo_dir: Path
    data: Data
    dry_run: bool

    @property
    def trash_dir(self) -> Path:
        return self.repo_dir / _trash_dir_name

    def find_targets(self) -> Iterator[Path]:
        include = self.data.tree.demand_subtree("tool.tyranno.targets")
        target_spec = GitIgnoreSpec.from_lines(include)
        gitignore_spec = self._gitignore_spec()
        for p in target_spec.match_tree(self.repo_dir):
            if not gitignore_spec.match_file(p):
                yield self.resolve_path(p)

    def find_trash(self) -> Iterator[Path]:
        include = self.data.tree.demand_subtree("tool.tyranno.trash")
        spec = GitIgnoreSpec.from_lines(include)
        for p in spec.match_tree(self.repo_dir):
            yield self.resolve_path(p)

    def resolve_path(self, path: Path | str) -> Path:
        path = Path(path).resolve(strict=True)
        if not str(path).startswith(str(self.repo_dir)):
            msg = f"{path} is not a descendent of {self.repo_dir}"
            raise AssertionError(msg)
        return path.relative_to(self.repo_dir)

    def _gitignore_spec(self):
        lines = (self.repo_dir / ".gitignore").read_text().splitlines()
        return GitIgnoreSpec.from_lines(lines)


@dataclass(frozen=True, slots=True)
class ContextFactory:
    def __call__(self, cwd: Path, dry_run: bool) -> Context:
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class DefaultContextFactory(ContextFactory):
    def __call__(self, cwd: Path, *, dry_run: bool) -> Context:
        read = Path("pyproject.toml").read_text(encoding="utf-8")
        tree = DotTree.from_nested(tomllib.loads(read))
        return Context(
            repo_dir=cwd,
            config=Data(tree),
            dry_run=dry_run,
        )
