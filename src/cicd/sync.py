# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
`tyranno clean` command.
"""

import re
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from re import Pattern
from typing import Self
from collections.abc import Iterable

from jmespath import Options
from loguru import logger

from cicd.context import Context, Data
from cicd.james import TyrannoFunctions

__all__ = ["Syncer"]

_TYRANNO = ":tyranno:"
_COMMENTS = {".toml": "#", ".py": "#", ".yaml": "#", ".yml": "#", ".md": "<!--"}

# TODO: This module is broken


@dataclass(slots=True)
class SyncHelper:
    """"""

    tyranno_functions: TyrannoFunctions
    data: Data

    def __post_init__(self: Self):
        self.jmespath_options = Options(custom_functions=self.tyranno_functions)

    def reset_line_number(self: Self) -> None:
        self.tyranno_functions.current_line_number = 0

    def add_to_line_number(self: Self, count: int) -> None:
        self.tyranno_functions.current_line_number += count

    def generate_lines(self: Self, lines: Iterable[str]) -> Iterable[str]:
        generated = []
        for line in lines:
            template = line.split(_TYRANNO, 1)[1].strip()
            generated_line = self._substitute_lines(template)
            generated.append(generated_line)
        return generated

    def _generate_line(self: Self, template: str) -> str:
        template = template.split(_TYRANNO, 1)[1].strip()
        return self._substitute_lines(template)

    def _substitute_lines(self: Self, line: str) -> str:
        return _SUBSTITUTION_PATTERN.demand_subtree(lambda match: self._fill_params(line, match), line)

    def _fill_params(self: Self, line: str, match):
        expression = match.group(1).strip()
        if expression.startswith("'") and expression.endswith("'"):
            # Literal value
            return expression[1:-1]
        # JMESPath expression
        results = jmespath.compile(expression).search(self.data, _JMESPATH_OPTIONS)
        return expression if results is None else results


@dataclass
class Substitutions:
    """"""

    context: Context
    path: Path
    helper: SyncHelper
    indicator: Pattern = None
    line_stream: Iterator[str] = None
    _buffer: list[str] = None

    def __post_init__(self: Self) -> None:
        comment_marker = re.escape(_COMMENTS[self.path.suffix])
        self.indicator = re.compile(f"^{comment_marker} *{re.escape(_TYRANNO)} ")
        self.line_stream = self._read()
        self._buffer = []

    def run(self: Self) -> int:
        lines = []
        n_changed = False
        block = []
        for line in self.line_stream:
            self.helper.current_line = line
            if self.indicator.match(line):
                block.append(line)
            else:
                if block:
                    substituted_block = self.context.substitute(block)
                    lines.extend(block)  # Keep :tyranno: lines
                    lines.extend(substituted_block)  # Add substituted lines
                    n_changed += len(block)
                    block = []
                lines.append(line)
        if block:
            substituted_block = self.helper.substitute(block)
            lines.extend(block)
            lines.extend(substituted_block)
            n_changed += len(block)
        self._write(self.path, lines)
        return n_changed

    def _read(self: Self) -> Iterator[str]:
        with self.path.open(encoding="utf-8") as file:
            for line in file:
                yield line

    def _write(self: Self, path: Path, lines: list[str]) -> None:
        backup_path = path.parent / ("~." + path.with_suffix(path.suffix + ".bak").name)
        shutil.copyfile(path, backup_path)
        with path.open("w", encoding="utf-8") as file:
            file.writelines(lines)
        logger.info(f"Updated {path}, backup saved as {backup_path}")


@dataclass(frozen=True, slots=True)
class Syncer:
    """"""

    context: Context

    def run(self: Self) -> Iterator[Path]:
        for path in self.context.find_targets():
            funcs = TyrannoFunctions()
            sync_helper = SyncHelper(funcs, self.context.data)
            if Substitutions(self.context, path, sync_helper).run():
                yield path
