# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Per-repo context."""

import re
import tomllib
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Final

import jmespath
from pathspec import GitIgnoreSpec

from tyranno_sandbox.dot_tree import DotTree, Toml
from tyranno_sandbox.james import TyrannoJmesFunctions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tyranno_sandbox._global_vars import GlobalVars

__all__ = ["Context", "ContextFactory", "Data", "DefaultContextFactory"]
SIMPLE_KEY_REGEX: Final = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*+)(\.([A-Za-z_][A-Za-z0-9_-]*+))*+")
# Match `${{group1}}` using a possessive `[^}]++` and `}` with a negative lookahead.
EXPR_REGEX: Final = re.compile(r"\$\{\{ (?P<expr>(?: [^}]++ | }(?!}) )*) }}", re.VERBOSE)


@dataclass(frozen=True, slots=True)
class Data:
    """A data source for `::tyranno::` comments."""

    tree: DotTree
    tyranno_functions: ClassVar[TyrannoJmesFunctions] = TyrannoJmesFunctions()

    @cached_property
    def _jmespath_options(self) -> jmespath.Options:
        return jmespath.Options(custom_functions=self.tyranno_functions)

    def get(self, key: str) -> Toml | None:
        return self.tree.get(key)

    def access(self, key: str) -> Toml:
        return self.tree.access(key)

    def replace_vars_in(self, template: str, *, in_key: str = "") -> str:
        def xyz(m: re.Match) -> str:
            return self.expand_var(m.group("expr"), in_key=in_key)

        return EXPR_REGEX.sub(xyz, template)

    def expand_var(self, expression: str, *, in_key: str = "") -> str:
        expression = expression.strip()
        if expression.startswith("~."):
            expression = "tool.tyranno.data" + expression
        if in_key and expression.startswith("."):
            expression = in_key + expression
        if SIMPLE_KEY_REGEX.fullmatch(expression):
            return self.tree.access(expression)
        return jmespath.compile(expression).search(self.tree, self._jmespath_options)


@dataclass(frozen=True, slots=True, kw_only=True)
class Context:
    """Container of `pyproject.toml` data, global vars, repo state, and app state."""

    env: GlobalVars
    repo_dir: Path
    data: Data
    dry_run: bool

    def bak_path(self, path: Path) -> Path:
        return self.bak_dir / path.parent.relative_to(self.repo_dir)

    def trash_path(self, path: Path) -> Path:
        return self.trash_dir / path.parent.relative_to(self.repo_dir)

    @property
    def bak_dir(self) -> Path:
        return self.repo_dir / self.env.tyranno_dir / "sync-bak"

    @property
    def trash_dir(self) -> Path:
        return self.repo_dir / self.env.tyranno_dir / "trashed"

    def find_targets(self) -> Iterator[Path]:
        include = self.data.tree.access_subtree("tool.tyranno.targets")
        target_spec = GitIgnoreSpec.from_lines(include)
        gitignore_spec = self._gitignore_spec()
        for p in target_spec.match_tree(self.repo_dir):
            if not gitignore_spec.match_file(p):
                yield self.resolve_path(p)

    def resolve_path(self, path: Path | str) -> Path:
        path = Path(path).resolve(strict=True)
        if not str(path).startswith(str(self.repo_dir)):
            msg = f"{path} is not a descendent of {self.repo_dir}"
            raise AssertionError(msg)
        return path.relative_to(self.repo_dir)

    def _gitignore_spec(self) -> GitIgnoreSpec:
        lines = (self.repo_dir / ".gitignore").read_text().splitlines()
        return GitIgnoreSpec.from_lines(lines)


class ContextFactory:
    """A [Context][] factory."""

    def __call__(self, cwd: Path, env: GlobalVars, *, dry_run: bool) -> Context:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class DefaultContextFactory(ContextFactory):
    """A [Context][] factory that reads from `pyproject.toml`."""

    def __call__(self, cwd: Path, env: GlobalVars, *, dry_run: bool) -> Context:
        read = Path("pyproject.toml").read_text(encoding="utf-8")
        tree = DotTree.from_nested(tomllib.loads(read))
        return Context(env=env, repo_dir=cwd, data=Data(tree), dry_run=dry_run)
