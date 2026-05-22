# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""`tyranno sync` command."""

import re
import shutil
from dataclasses import dataclass, field
from functools import cache
from re import Pattern
from typing import TYPE_CHECKING, Final, Literal, NamedTuple, NewType, Self

from loguru import logger

from tyranno_sandbox.context import ExpressionError

if TYPE_CHECKING:
    from pathlib import Path

    from tyranno_sandbox.context import Context


@dataclass(frozen=True, kw_only=True)
class Tokens:
    """Regex generator and memoizer for Tyranno comments."""

    tyranno_inline: str
    tyranno_block_start: str
    tyranno_block_end: str

    @classmethod
    def create(cls) -> Self:
        return cls(
            tyranno_inline="::tyranno::",
            tyranno_block_start="::tyranno start::",
            tyranno_block_end="::tyranno end::",
        )

    @cache  # noqa: B019
    def inline_regex(self, comment_start: str, comment_end: str) -> Pattern[str]:
        """Build a regex matching a single `::tyranno::` comment line.

        The named group `line` captures everything between the marker and the
        (optional) comment-close token, so that the caller can extract and
        evaluate the template expression.
        """
        # Allow any leading whitespace (for indented comment lines).
        start_seq = (
            r"\s*"
            + re.escape(comment_start)
            + r"\s*"
            + re.escape(self.tyranno_inline)
        )
        # Everything up to (but not including) the comment-close token.
        if comment_end:
            capture = r".*?"
            end_seq = re.escape(comment_end) + r".*"
        else:
            capture = r".*"
            end_seq = ""
        return re.compile(rf"^{start_seq}(?P<line>{capture}){end_seq}$")


TOKENS: Final = Tokens.create()

Suffix = NewType("Suffix", str)


class CommentTokenPair(NamedTuple):
    """Start and optional end comment tokens (e.g. ``("//", "")``).

    - If ``end == ""``, the comment is single-line.
    - If ``end != ""``, the comment is multi-line.
    """

    start: str
    end: str

    @property
    def is_multiline(self) -> bool:
        return bool(self.end)


def get_comment_tokens() -> dict[Suffix, CommentTokenPair]:
    pound = {".toml", ".yaml", ".yml", ".sh", "CITATION.cff", "Dockerfile", "justfile"}
    ignore = {".gitignore", ".dockerignore", ".helmignore", ".prettierignore", ".editorconfig"}
    slash = {".java", ".scala", ".ks", ".c", ".cpp", ".js", ".ts", ".py"}
    semicolon = {".ini", ".antlr"}
    html_like = {".md", ".html"}
    css_like = {".css", ".less", ".sass", ".scss"}
    return {
        **dict.fromkeys(map(Suffix, pound), CommentTokenPair("#", "")),
        **dict.fromkeys(map(Suffix, ignore), CommentTokenPair("#", "")),
        **dict.fromkeys(map(Suffix, slash), CommentTokenPair("//", "")),
        **dict.fromkeys(map(Suffix, semicolon), CommentTokenPair(";", "")),
        **dict.fromkeys(map(Suffix, html_like), CommentTokenPair("<!--", "-->")),
        **dict.fromkeys(map(Suffix, css_like), CommentTokenPair("/*", "*/")),
    }


_COMMENTS: Final[dict[Suffix, CommentTokenPair]] = get_comment_tokens()


class DeltaLine(NamedTuple):
    """A single generated line, alongside the original."""

    template: str
    old_line: str | None
    new_line: str | None

    @property
    def is_modified(self) -> bool:
        return self.old_line != self.new_line


@dataclass(frozen=True)
class DeltaBlock:
    """One or more generated lines, alongside the original lines."""

    kind: Literal["inline", "block"]
    path: Path
    first_line_number: int
    templates: list[str]
    old_lines: list[str | None]
    new_lines: list[str | None]

    def __len__(self) -> int:
        return len(self.templates)

    def __getitem__(self, index: int) -> DeltaLine:
        return DeltaLine(self.templates[index], self.old_lines[index], self.new_lines[index])

    @property
    def last_line_number(self) -> int:
        return self.first_line_number + len(self)

    @property
    def n_lines_differ(self) -> int:
        return sum(o != n for o, n in zip(self.old_lines, self.new_lines, strict=False))

    def __str__(self) -> str:
        if self.kind == "block":
            return repr(self)
        l0, ln = self.first_line_number, self.last_line_number
        ob, nb = self.old_lines, self.new_lines
        if len(nb) == 1 and nb == ob:
            return f"Line {l0} unchanged."
        if len(nb) == 1:
            return f"Line {l0} edited from '{ob[0]}' to '{nb[0]}'."
        if nb == ob:
            return f"Lines {l0} to {ln} unchanged."
        return f"Lines {l0} to {ln} edited ({self.n_lines_differ} lines differ)."


@dataclass(slots=True)
class SyncHelper:
    """Substitutes `::tyranno::` template comments in a single file.

    After calling [run][], inspect [new_lines][] for the output content and
    [hits][] for a summary of what changed.
    """

    context: Context
    path: Path
    _pattern: Pattern[str] = field(init=False)
    _new_lines: list[str] = field(default_factory=list, init=False)
    _hits: list[DeltaBlock] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        tokens = _COMMENTS[Suffix(self.path.suffix or self.path.name)]
        self._pattern = TOKENS.inline_regex(tokens.start, tokens.end)

    @property
    def new_lines(self) -> list[str]:
        return self._new_lines

    @property
    def hits(self) -> list[DeltaBlock]:
        return self._hits

    def run(self) -> None:
        """Process the file line-by-line, expanding `::tyranno::` expressions."""
        lines = self.path.read_text(encoding="utf-8").splitlines()
        result: list[str] = []
        i = 0
        while i < len(lines):
            m = self._pattern.fullmatch(lines[i].rstrip())
            if not m:
                result.append(lines[i])
                i += 1
                continue

            # Collect consecutive ::tyranno:: comment lines.
            first_line = i
            header_lines: list[str] = [lines[i]]
            expressions: list[str] = [m.group("line").strip()]
            i += 1
            while i < len(lines):
                m2 = self._pattern.fullmatch(lines[i].rstrip())
                if not m2:
                    break
                header_lines.append(lines[i])
                expressions.append(m2.group("line").strip())
                i += 1

            # Keep the ::tyranno:: comment lines verbatim.
            result.extend(header_lines)

            # Consume old content lines (one per template) and emit new ones.
            n = len(expressions)
            old_lines = lines[i : i + n]
            i += n
            new_lines: list[str] = []
            content_start = first_line + len(header_lines) + 1  # 1-based line number
            for idx, expr in enumerate(expressions):
                try:
                    new_lines.append(self.context.data.replace_vars_in(expr))
                except ExpressionError as e:
                    logger.error(f"{self.path}:{content_start + idx}: {e}")
                    new_lines.append(old_lines[idx] if idx < len(old_lines) else "")
            result.extend(new_lines)

            self._hits.append(
                DeltaBlock("inline", self.path, first_line, expressions, old_lines, new_lines)
            )

        self._new_lines = result


@dataclass(frozen=True, slots=True)
class Syncer:
    """Entry point that syncs files."""

    context: Context
    backup: bool = False

    def run(self) -> None:
        for path in self.context.find_targets():
            suffix = Suffix(path.suffix or path.name)
            if suffix not in _COMMENTS:
                logger.debug(f"Skipping {path}: no comment tokens defined for suffix '{suffix}'")
                continue
            self.run_on(path)

    def run_on(self, path: Path) -> None:
        helper = SyncHelper(self.context, path)
        helper.run()
        if not self.context.dry_run:
            self._save(path, helper.new_lines)
        self._log(path, helper.hits)

    def _save(self, path: Path, lines: list[str]) -> None:
        if self.backup:
            bak_path = self.context.bak_path(path)
            bak_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, bak_path)
        self._write(path, lines)

    def _log(self, path: Path, hits: list[DeltaBlock]) -> None:
        for hit in hits:
            logger.debug(str(hit))
        bak_msg = f" (backup: {self.context.bak_path(path)})" if self.backup else ""
        n_differ = sum(hit.n_lines_differ for hit in hits)
        n_total = sum(len(hit) for hit in hits)
        n_blocks = len(hits)
        logger.info(
            f"Processed {path}: {n_differ} lines changed"
            f" (of {n_total} in {n_blocks} blocks){bak_msg}"
        )

    def _write(self, path: Path, lines: list[str]) -> None:
        content = "\n".join(lines) + "\n"
        temp_file = path.with_name(f".~{path.name}.temp")
        try:
            temp_file.write_text(content, encoding="utf-8")
            shutil.move(str(temp_file), str(path))
        finally:
            temp_file.unlink(missing_ok=True)
