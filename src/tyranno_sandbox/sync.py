# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
`tyranno sync` command.
"""

import re
import shutil
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from re import Pattern

import jmespath
from loguru import logger

from tyranno_sandbox.context import Context, Data
from tyranno_sandbox.james import TyrannoFunctions

__all__ = ["Syncer"]
_TYRANNO = ":tyranno:"
_SINGLE_LINE_COMMENT_MARKERS: dict[str, tuple[str, str]] = {
    "*.toml": ("#", ""),
    "*.java": ("//", ""),
    "*.scala": ("//", ""),
    "*.ks": ("//", ""),
    "*.c": ("//", ""),
    "*.cpp": ("//", ""),
    "*.js": ("//", ""),
    "*.ts": ("//", ""),
    "*.py": ("#", ""),
    "*.sh": ("#", ""),
    "*.css": ("#", ""),
    "*.yaml": ("#", ""),
    "*.yml": ("#", ""),
    "*.ini": (";", ""),
    "*.antlr": (";", ""),
    "*.md": ("<!--", "-->"),  # Also multiline, but that's ok.
    "*.html": ("<!--", "-->"),  # Also multiline, but that's ok.
    "justfile": ("#", ""),
    "CITATION.cff": ("#", ""),
}
# Match `${{group1}}` using a possessive `[^}]++` and `}` with a negative lookahead.
_SUBSTITUTION_PATTERN: re.Pattern = re.compile(r"\$\{\{ ((?: [^}]++ | }(?!}) )*) }}", re.VERBOSE)


@dataclass(frozen=True, slots=True)
class SyncHit:
    path: Path
    line_number: int
    old_block: list[str]
    new_block: list[str]

    @property
    def n_lines_changed(self) -> int:
        return sum(i == j for i, j in zip(self.old_block, self.new_block, strict=False))

    def __str__(self) -> str:
        ln, ob, nb = self.line_number, self.old_block, self.new_block
        if len(nb) == 1 and nb == ob:
            return f"Line {ln} unchanged."
        if len(nb) == 1:
            return f"Line {ln} edited from '{ob[0]}' to '{nb[0]}'."
        if nb == ob:
            return f"Lines {ln - len(nb)} to {ln} unchanged."
        return f"Lines {ln - len(nb)} to {ln} edited ({self.n_lines_changed} lines differ)."


@dataclass(frozen=True)
class SyncHelper:
    """"""

    tyranno_functions: TyrannoFunctions
    data: Data

    @cached_property
    def _jmespath_options(self) -> jmespath.Options:
        return jmespath.Options(custom_functions=self.tyranno_functions)

    def generate_lines(self, lines: list[str]) -> list[str]:
        generated = []
        for line in lines:
            template = line.split(_TYRANNO, 1)[1].strip()
            generated_line = self._substitute_lines(template)
            generated.append(generated_line)
        return generated

    def _generate_line(self, template: str) -> str:
        template = template.split(_TYRANNO, 1)[1].strip()
        return self._substitute_lines(template)

    def _substitute_lines(self, line: str) -> str:
        return _SUBSTITUTION_PATTERN.sub(lambda match: self._fill_params(match), line)

    def _fill_params(self, match: re.Match):
        expression = str(match.group(1))
        results = jmespath.compile(expression).search(self.data, self._jmespath_options)
        return expression if results is None else results


@dataclass
class Substitutions:
    """"""

    context: Context
    path: Path
    helper: SyncHelper
    indicator: Pattern = re.compile(r".")  # Filled in by `__post_init__`.
    _old_lines: list[str] = field(default_factory=list)  # Filled in by `__post_init__`.
    _new_lines: list[str] = field(default_factory=list)
    _buffer: list[str] = field(default_factory=list)
    _line_number: int = 0  # Start at line #0 (let str messages add + 1).
    _buffer_countdown: int = 0

    def __post_init__(self) -> None:
        start, end = _SINGLE_LINE_COMMENT_MARKERS[self.path.suffix]
        self.indicator = re.compile(rf"^\s*{re.escape(start)}\s*{re.escape(_TYRANNO)}\s*{re.escape(end)}")
        self._old_lines = self.path.read_text().splitlines() + [""]
        self._buffer = []

    def __next__(self) -> SyncHit:
        while not (s := self._next()):
            pass
        return s

    def _next(self) -> SyncHit | None:
        line = self._old_lines[self._line_number]
        if self._buffer_countdown > 1:
            self._buffer_countdown -= 1
        elif self._buffer_countdown == 1:
            original = self._old_lines[self._line_number - len(self._buffer) :]
            return SyncHit(self.path, self._line_number, original, self._buffer)
        elif self.indicator.match(line):
            self._buffer.append(line)
        else:
            self._new_lines += self._buffer
            self._new_lines.append(line)
            self._buffer_countdown = len(self._buffer)
        self._line_number += 1

    def _write(self, path: Path, lines: list[str]) -> None:
        backup_path = path.parent / (".~" + path.with_suffix(path.suffix + ".bak").name)
        shutil.copyfile(path, backup_path)
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Updated %s, backup saved as %s", path, backup_path)


@dataclass(frozen=True, slots=True)
class Syncer:
    """"""

    context: Context

    def run(self) -> Iterator[Path]:
        funcs = TyrannoFunctions()
        sync_helper = SyncHelper(funcs, self.context.data)
        for path in self.context.find_targets():
            if Substitutions(self.context, path, sync_helper).run():
                yield path
