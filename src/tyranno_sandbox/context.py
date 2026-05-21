# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Per-repo context."""

import re
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pathspec import GitIgnoreSpec

from tyranno_sandbox.dot_tree import DotTree, Toml

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tyranno_sandbox._global_vars import GlobalVars

__all__ = ["Context", "ContextFactory", "Data", "DefaultContextFactory"]

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
        - Simple key paths: ``project.name``, ``.vendor``
        - Pipe syntax:  ``project.keywords | yaml(@)``
        - Chained functions: ``project.description.yaml(@)``
        - Standalone calls: ``now_utc().year``
        """
        expression = expression.strip()
        if not expression:
            return ""

        # Pipe syntax: split on | and process left-to-right
        if "|" in expression:
            parts = _PIPE_SPLIT_RE.split(expression)
            value = self._resolve_key(parts[0].strip(), in_key=in_key)
            for func_call in parts[1:]:
                value = self._apply_func(func_call.strip(), value)
            return value

        # Compact dot-chained syntax: project.description.yaml(@)
        # Split into key path + trailing function calls
        key_part, func_calls = self._parse_chained(expression, in_key=in_key)

        # If key_part is empty the whole expression is a standalone function chain
        # (e.g. "now_utc().year") — reconstruct and evaluate directly.
        if not key_part and func_calls:
            return self._resolve_key(".".join(func_calls), in_key=in_key)

        value = self._resolve_key(key_part, in_key=in_key)
        for fc in func_calls:
            value = self._apply_func(fc, value)
        return value

    def _parse_chained(self, expr: str, *, in_key: str = "") -> tuple[str, list[str]]:
        """Split ``key.func1(args).func2(args)`` into key + function list."""
        # Collapse spaces in "$ .project .name" style
        if re.search(r"\s", expr):
            expr = re.sub(r"\s*\.\s*", ".", re.sub(r"\s+", " ", expr)).strip()

        # Walk dot-segments left to right; once a segment has "(" it's a func call
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

        # Keep empty leading string so that ".frag" → key ".frag", not "frag"
        return ".".join(key_segs), func_calls

    def _resolve_key(self, expr: str, *, in_key: str = "") -> str:
        """Resolve a key expression (no function calls) to a string value."""
        expr = expr.strip()
        if not expr:
            return ""

        # Standalone function call: now_utc().year  /  now_local()
        if "(" in expr:
            return self._eval_standalone(expr)

        # Strip file-local marker
        if expr.startswith("^"):
            expr = expr[1:]

        # Normalise prefix to a plain dotted key
        if expr.startswith("$."):
            simple_key = expr[2:]
        elif expr.startswith("@."):
            simple_key = "tool.tyranno.data." + expr[2:]
        elif expr.startswith("."):
            simple_key = (in_key + expr) if in_key else ("tool.tyranno.data" + expr)
        elif expr == "$":
            return ""
        else:
            simple_key = expr

        # Fast path: plain dotted key
        if SIMPLE_KEY_REGEX.fullmatch(simple_key):
            try:
                value = self.tree.access(simple_key)
                return self._to_str(value)
            except (KeyError, TypeError):
                pass

        # Fallback: JSONPath via jsonpath_ng
        try:
            from jsonpath_ng import parse as jsonpath_parse  # noqa: PLC0415

            jpath = expr if expr.startswith("$") else f"$.{simple_key}"
            matches = jsonpath_parse(jpath).find(dict(self.tree))
            if matches:
                return self._to_str(matches[0].value)
        except Exception:  # noqa: BLE001
            pass

        return f"<unresolved:{expr}>"

    def _eval_standalone(self, expr: str) -> str:
        """Evaluate a standalone function call expression like ``now_utc().year``."""
        # now_utc() and now_local() return a dict-like with year/month/day etc.
        now_utc = datetime.now(UTC)
        now_local = datetime.now().astimezone()

        known: dict[str, object] = {
            "now_utc()": now_utc,
            "now_local()": now_local,
        }
        # Check for attribute access: now_utc().year
        for prefix, dt_obj in known.items():
            if expr.startswith(prefix):
                rest = expr[len(prefix):]
                if rest.startswith("."):
                    attr = rest[1:]
                    return str(getattr(dt_obj, attr, f"<no attr {attr}>"))
                if not rest:
                    return str(dt_obj)
        return f"<unresolved:{expr}>"

    @staticmethod
    def _apply_func(func_call: str, value: str) -> str:
        """Apply a single function call like ``yaml(@)`` to ``value``."""
        func_call = func_call.strip()
        m = _FUNC_CALL_RE.fullmatch(func_call)
        if not m:
            return value

        name = m.group(1)
        raw_args = [a.strip() for a in m.group(2).split(",") if a.strip()]
        # Replace @ with the current value in positional args
        args = [value if a == "@" else a.strip("'\"") for a in raw_args]

        match name:
            case "yaml":
                return Data._yaml_scalar(value)
            case "yaml_multiline":
                indent = int(args[1]) if len(args) > 1 else 0
                return Data._yaml_seq_multiline(value, indent)
            case "lower":
                return value.lower()
            case "upper":
                return value.upper()
            case "replace":
                # replace(@, old, new) — args[0] is @ (value), [1] is old, [2] is new
                if len(args) >= 3:  # noqa: PLR2004
                    return args[0].replace(args[1], args[2])
            case "spdx_license":
                # Return the SPDX identifier itself — license data lookup is unimplemented
                return value
            case "pep440_minor":
                try:
                    from packaging.version import Version  # noqa: PLC0415

                    v = Version(value)
                    return f"{v.major}.{v.minor}"
                except Exception:  # noqa: BLE001
                    return value
            case "sort":
                items = [i.strip() for i in value.split(",")]
                return ", ".join(sorted(items))
            case "join":
                # join(sep, @) — args[0] is sep, args[1] is @ (value)
                sep = args[0] if args else ", "
                items = [i.strip() for i in value.split(",")]
                return sep.join(items)
        return value

    @staticmethod
    def _yaml_scalar(value: str) -> str:
        """Quote a string as a YAML scalar if necessary."""
        needs_quoting = (
            not value
            or value[0] in "#&*?|->!%@`'\""
            or any(c in value for c in ":#\n{[")
            or value.lower() in {"true", "false", "null", "yes", "no", "on", "off"}
        )
        if needs_quoting:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return value

    @staticmethod
    def _yaml_seq_multiline(value: str, indent: int = 0) -> str:
        """Format a comma-separated value as an indented YAML sequence block."""
        pad = " " * indent
        items = [v.strip() for v in value.split(",") if v.strip()]
        return "\n".join(f'{pad}"{item}"' for item in items)

    @staticmethod
    def _to_str(value: Toml) -> str:
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
