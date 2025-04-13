# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
`tyranno sync` command.
"""

import re
import shutil
from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cache, cached_property
from pathlib import Path
from re import Pattern
from typing import Final, Literal, NamedTuple, Self

from loguru import logger

from tyranno_sandbox.context import Context


@dataclass(frozen=True, kw_only=True)
class Markers:
    """Regex generator and memoizer for Tyranno comments."""

    tyranno_inline: str
    tyranno_block_start: str
    tyranno_block_end: str

    @classmethod
    def create(cls) -> Self:
        return cls(
            tyranno_inline="::tyranno::",
            tyranno_block_start="::tyranno block start::",
            tyranno_block_end="::tyranno block end::",
        )

    @cache  # noqa: B019
    def inline_regex(self, comment_start: str, comment_end: str) -> Pattern[str]:
        capture = self._fast_lazy_pattern(comment_end)
        start_seq = re.escape(comment_start) + r"\s*" + re.escape(self.tyranno_inline)
        # To allow possessive matching, we'll remove trailing whitespace after capture.
        # So we don't need `\s*` here.
        # But we do want to allow text after a comment end sequence.
        # For example, this is ok: `<!-- ::tyranno:: ... --><!-- see above ... -->`.
        end_seq = f"{re.escape(comment_end)}.*" if comment_end else ""
        return re.compile(rf"^{start_seq}(?P<line>{capture}){end_seq}$")

    def _fast_lazy_pattern(self, end_marker: str, *, lazy: bool = False) -> str:
        end_tokens: list[str] = [re.escape(t) for t in end_marker]
        match len(end_tokens):
            case 0:
                # language=regexp
                pattern = ".*+"
            case 1 if lazy:
                # language=regexp
                pattern = r"[^⸨T0⸩]+"
            case 1:
                # language=regexp
                pattern = r"[^⸨T0⸩]++"
            case _ if lazy:
                # language=regexp
                pattern = r"(?:[^⸨T*⸩]++|[⸨T*⸩]+)*"
            case _:
                # language=regexp
                pattern = r"(?:[^⸨T0⸩]++|⸨T0⸩(?!⸨T≽1⸩))*"
        re.compile(r"⸨T(\d++)⸩").sub(lambda m: end_tokens[int(m.group(1))], pattern)
        re.compile(r"⸨T≽(\d++)⸩").sub(lambda m: "".join(end_tokens[int(m.group(1)) :]), pattern)
        re.compile(r"⸨T\*⸩").sub("".join(set(end_tokens)), pattern)
        return pattern


MARKERS: Final[Markers] = Markers.create()


def get_comment_markers() -> dict[str, tuple[str, str]]:
    pound: set[str] = {".toml", ".yaml", ".yml", ".sh", "CITATION.cff", "Dockerfile", "justfile"}
    ignore: set[str] = {".gitignore", ".dockerignore", ".helmignore", ".prettierignore", ".editorconfig"}
    slash: set[str] = {".java", ".scala", ".ks", ".c", ".cpp", ".js", ".ts", ".py"}
    semicolon: set[str] = {".ini", ".antlr"}
    html_like: set[str] = {".md", ".html"}
    css_like: set[str] = {".css", ".less", ".sass", ".scss"}
    return {
        **dict.fromkeys(pound, ("#", "")),
        **dict.fromkeys(ignore, ("#", "")),
        **dict.fromkeys(slash, ("//", "")),
        **dict.fromkeys(semicolon, (";", "")),
        **dict.fromkeys(html_like, ("<!--", "-->")),
        **dict.fromkeys(css_like, ("/*", "*/")),
    }


_COMMENTS: Final[dict[str, tuple[str, str]]] = get_comment_markers()


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

    @cached_property
    def last_line_number(self) -> int:
        return self.first_line_number + len(self)

    @cached_property
    def n_lines_differ(self) -> int:
        return sum(i == j for i, j in zip(self.old_lines, self.new_lines, strict=False))

    def __str__(self) -> str:
        if self.kind == "block":
            return repr(self)  # TODO
        l0, ln, ob, nb = self.first_line_number, self.last_line_number, self.old_lines, self.new_lines
        if len(nb) == 1 and nb == ob:
            return f"Line {l0} unchanged."
        if len(nb) == 1:
            return f"Line {l0} edited from '{ob[0]}' to '{nb[0]}'."
        if nb == ob:
            return f"Lines {l0} to {ln} unchanged."
        return f"Lines {l0} to {ln} edited ({self.n_lines_differ} lines differ)."


@dataclass(slots=True)
class SyncHelper:
    """Utility that substitutes `::tyranno::` comments in a file."""

    context: Context
    path: Path
    # Filled in by `__post_init__`.
    _pattern: Pattern = field(init=False)
    _line_number: int = field(default=0, init=False)  # Start at line #0 (let str messages add + 1).
    _old_lines: list[str] = field(default_factory=list, init=False)  # don't modify
    _new_lines: list[str] = field(default_factory=list, init=False)
    _templates: list[str] = field(default_factory=list, init=False)
    _template_rewind: int = field(default=-1, init=False)
    _hits: list[DeltaBlock] = field(default_factory=list, init=False)

    @property
    def new_lines(self) -> list[str]:
        return self._new_lines

    @property
    def hits(self) -> list[DeltaBlock]:
        return self._hits

    def __post_init__(self) -> None:
        start, end = _COMMENTS[self.path.suffix or self.path.name]
        self._pattern = MARKERS.inline_regex(start, end)
        self._old_lines = [*self.path.read_text().splitlines(), ""]

    def run(self) -> None:
        for _ in range(len(self._old_lines)):
            if hit := self._next_line():
                self._hits.append(hit)
            self._line_number += 1

    def _next_line(self) -> DeltaBlock | None:
        line = self._old_lines[self._line_number]
        if self._template_rewind > 0:  # Skip this line, which will be replaced (eat at the buffer)
            self._template_rewind -= 1
        elif self._template_rewind == 0:  # We finished the skipped lines (ate the whole buffer)
            original = self._old_lines[self._line_number - len(self._templates) : self._line_number]
            new = list(self._generate_lines(self._templates))
            self._new_lines += new
            buffer = list(self._templates)
            self._templates = []
            self._template_rewind = -1
            return DeltaBlock("inline", self.path, self._line_number, buffer, original, new)
        elif m := self._pattern.fullmatch(line):  # We're in a block: start or add to a buffer
            self._templates.append(m.group("capture"))
        elif self._templates:  # It's the first real line after a block
            self._template_rewind = len(self._templates)  # Begin eating the buffer
            self._templates.append(line)  # Include the first real line, too (it'll be used as-is)
        else:
            self._new_lines.append(line)
        return None

    def _generate_lines(self, templates: list[str]) -> Generator[str]:
        for template in templates:
            yield self.context.data.replace_vars_in(template)


@dataclass(frozen=True, slots=True)
class Syncer:
    """Entry point that syncs files."""

    context: Context
    atomic: bool = False
    backup: bool = False

    def run(self) -> None:
        for path in self.context.find_targets():
            self.run_on(path)

    def run_on(self, path: Path) -> None:
        helper = SyncHelper(self.context, path)
        helper.run()
        self._save(path, helper.new_lines)
        self._log(path, helper.hits)

    def _save(self, path: Path, lines: list[str]) -> None:
        if self.backup:
            bak_path = self.context.bak_path(path) if self.backup else None
            shutil.copyfile(path, bak_path)
        self._write(path, lines)

    def _log(self, path: Path, hits: list[DeltaBlock]) -> None:
        for hit in hits:
            logger.debug(hit)
        bak_path = self.context.bak_path(path) if self.backup else None
        logger.info(
            "Updated %s: %i lines changed (of %i in %i blocks)%s"
            + (f" (backup saved as {bak_path})" if bak_path else " (no backup created)"),
            path,
            sum(hit.n_lines_differ for hit in hits),
            sum(len(hit) for hit in hits),
            len(hits),
        )

    def _write(self, path: Path, lines: list[str]) -> None:
        if self.atomic:
            self._write_atomic(path, lines)
        else:
            path.write_text("\n".join(lines), encoding="utf-8")

    def _write_atomic(self, path: Path, lines: list[str]) -> None:
        temp_file = path.with_name(f".~{path.name}.temp")
        try:
            temp_file.write_text("\n".join(lines), encoding="utf-8")
            shutil.move(temp_file, path)
        finally:
            temp_file.unlink(missing_ok=True)
