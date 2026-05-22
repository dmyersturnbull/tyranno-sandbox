# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Per-repo context."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from jsonpath_ng import parse as jsonpath_parse
from pathspec import GitIgnoreSpec

from tyranno_sandbox.dot_tree import DotTree, Toml
from tyranno_sandbox.tyranno_functions import FUNCS, SOURCE_FUNCS

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tyranno_sandbox._global_vars import GlobalVars

__all__ = ["Context", "ContextFactory", "Data", "DefaultContextFactory", "ExpressionError"]

# ── Regex patterns (all pre-compiled) ────────────────────────────────────────

# Match simple dotted key names like `project.name` or `tool.tyranno.data.vendor`
SIMPLE_KEY_REGEX: Final = re.compile(
    r"[A-Za-z_][A-Za-z0-9_-]*+(?:\.[A-Za-z_][A-Za-z0-9_-]*+)*+"
)

# Match `$<<expr>>` using a non-greedy inner pattern
EXPR_REGEX: Final = re.compile(r"\$<<(?P<expr>.*?)>>", re.DOTALL)

# Match a function call: name(args...)
_FUNC_CALL_RE: Final = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)$")

# Split a pipe chain:  a | b | c
_PIPE_SPLIT_RE: Final = re.compile(r"\s*\|\s*")

# Collapse whitespace around dots for spaced key notation:  "$ .project .name"
_WS_DOT_RE: Final = re.compile(r"\s*\.\s*")
_MULTI_SPACE_RE: Final = re.compile(r"\s+")

# ── Key prefix constants ──────────────────────────────────────────────────────

_PREFIX_ROOT: Final = "$."       # $.key → pyproject root key
_PREFIX_AT: Final = "@."         # @.key → tool.tyranno.data.key
_PREFIX_LOCAL: Final = "."       # .key → relative to in_key context
_ROOT_ONLY: Final = "$"          # bare "$" → empty string
_MARKER_FILE_LOCAL: Final = "^"  # ^key → strip this marker (file-local reference)


class ExpressionError(Exception):
    """Raised when a Tyranno template expression cannot be evaluated."""


@dataclass(frozen=True, slots=True)
class Data:
    """A data source for `::tyranno::` comments."""

    tree: DotTree

    def get(self, key: str) -> Toml | None:
        return self.tree.get(key)

    def access(self, key: str) -> Toml:
        return self.tree.access(key)

    def replace_vars_in(self, template: str, *, in_key: str = "") -> str:
        def _expand(m: re.Match) -> str:
            return self.expand_var(m.group("expr"), in_key=in_key)

        return EXPR_REGEX.sub(_expand, template)

    # ------------------------------------------------------------------
    # Expression evaluation
    # ------------------------------------------------------------------

    def expand_var(self, expression: str, *, in_key: str = "") -> str:
        """Evaluate a single expression from inside ``$<< >>``.

        Handles:
        - Simple key paths: `project.name`, `.vendor`
        - Pipe syntax: `project.keywords | yaml(@)`
        - Chained functions: `project.description | yaml(@)`
        - Standalone calls: `now_utc().year`
        """
        expression = expression.strip()
        if not expression:
            return ""

        # Pipe syntax: split on | and process left-to-right
        if "|" in expression:
            parts = _PIPE_SPLIT_RE.split(expression)
            first = parts[0].strip()
            value: Any = (
                self._apply_func(first, None) if "(" in first else self._resolve_key(first, in_key=in_key)
            )
            for func_call in parts[1:]:
                value = self._apply_func(func_call.strip(), value)
            return self._to_str(value)

        # Compact dot-chained syntax: key.func1(args).func2(args)
        key_part, func_calls = self._parse_chained(expression)
        value = None if not key_part else self._resolve_key(key_part, in_key=in_key)
        for fc in func_calls:
            value = self._apply_func(fc, value)
        return self._to_str(value) if value is not None else ""

    def _parse_chained(self, expr: str) -> tuple[str, list[str]]:
        """Split `key.func1(args).func2(args)` into a key path and function list."""
        if re.search(r"\s", expr):
            expr = _WS_DOT_RE.sub(".", _MULTI_SPACE_RE.sub(" ", expr)).strip()

        segments = expr.split(".")
        key_segs: list[str] = []
        func_calls: list[str] = []
        in_funcs = False
        for seg in segments:
            if in_funcs or ("(" in seg):
                if seg:
                    func_calls.append(seg)
                in_funcs = True
            else:
                key_segs.append(seg)

        # Preserve empty leading element so `.frag` → `".frag"` not `"frag"`
        return ".".join(key_segs), func_calls

    def _resolve_key(self, expr: str, *, in_key: str = "") -> Any:
        """Resolve a dotted key expression to its raw value in the tree."""
        expr = expr.strip()
        if not expr:
            return ""

        if expr.startswith(_PREFIX_ROOT):
            simple_key = expr[2:]
        elif expr.startswith(_PREFIX_AT):
            simple_key = "tool.tyranno.data." + expr[2:]
        elif expr.startswith(_PREFIX_LOCAL):
            simple_key = (in_key + expr) if in_key else ("tool.tyranno.data" + expr)
        elif expr == _ROOT_ONLY:
            return ""
        else:
            simple_key = expr.removeprefix(_MARKER_FILE_LOCAL)

        if SIMPLE_KEY_REGEX.fullmatch(simple_key):
            try:
                return self.tree.access(simple_key)
            except (KeyError, TypeError) as e:
                raise ExpressionError(f"Key not found: {simple_key!r}") from e

        jpath = expr if expr.startswith("$") else f"$.{simple_key}"
        try:
            matches = jsonpath_parse(jpath).find(dict(self.tree))
            if matches:
                return matches[0].value
        except Exception as e:
            raise ExpressionError(f"Key not found: {expr!r}") from e
        raise ExpressionError(f"Key not found: {expr!r}")

    def _apply_func(self, func_call: str, value: Any) -> Any:
        """Apply a single function call like `yaml(@)` or attribute access like `year`."""
        func_call = func_call.strip()
        if m := _FUNC_CALL_RE.fullmatch(func_call):
            name = m.group(1)
            raw_args = [a.strip() for a in m.group(2).split(",") if a.strip()]
            # `@` is the value placeholder; strip it — value is always passed as first arg
            extra_args = [a.strip("'\"") for a in raw_args if a != "@"]
            if name in SOURCE_FUNCS:
                return SOURCE_FUNCS[name](*extra_args)
            if name in FUNCS:
                return FUNCS[name](value, *extra_args)
            raise ExpressionError(f"Unknown function: {name!r}")
        # No parentheses: treat as attribute access on the current value
        try:
            return getattr(value, func_call)
        except AttributeError:
            raise ExpressionError(f"No attribute {func_call!r} on {type(value).__name__}")

    @staticmethod
    def _to_str(value: Any) -> str:
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class Context:
    """Container of `pyproject.toml` data, global vars, repo state, and app state."""

    env: GlobalVars
    repo_dir: Path
    data: Data
    dry_run: bool

    def bak_path(self, path: Path) -> Path:
        return self.bak_dir / path.relative_to(self.repo_dir)

    def trash_path(self, path: Path) -> Path:
        return self.trash_dir / path.relative_to(self.repo_dir)

    @property
    def bak_dir(self) -> Path:
        return self.repo_dir / self.env.tyranno_dir / "sync-bak"

    @property
    def trash_dir(self) -> Path:
        return self.repo_dir / self.env.tyranno_dir / "trashed"

    def find_targets(self) -> Iterator[Path]:
        include = self.data.tree.get_list_as("tool.tyranno.targets", as_type=str)
        target_spec = GitIgnoreSpec.from_lines(include)
        gitignore_spec = self._gitignore_spec()
        for p in target_spec.match_tree_files(str(self.repo_dir)):
            if not gitignore_spec.match_file(p):
                yield self.repo_dir / p

    def _gitignore_spec(self) -> GitIgnoreSpec:
        gitignore = self.repo_dir / ".gitignore"
        lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
        return GitIgnoreSpec.from_lines(lines)


class ContextFactory:
    """A [Context][] factory."""

    def __call__(self, cwd: Path, env: GlobalVars, *, dry_run: bool) -> Context:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class DefaultContextFactory(ContextFactory):
    """A [Context][] factory that reads from `pyproject.toml`."""

    def __call__(self, cwd: Path, env: GlobalVars, *, dry_run: bool) -> Context:
        read = (cwd / "pyproject.toml").read_text(encoding="utf-8")
        tree = DotTree.from_nested(tomllib.loads(read))
        return Context(env=env, repo_dir=cwd, data=Data(tree), dry_run=dry_run)
