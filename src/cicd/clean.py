# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
`tyranno clean` command.
"""

import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from cicd.context import Context

__all__ = ["Cleaner"]


@dataclass(frozen=True, slots=True)
class Cleaner:
    """"""

    context: Context

    def run(self: Self) -> Iterator[Path]:
        for path in self.context.find_trash():
            self._trash(path)
            yield path

    def _trash(self: Self, source: Path) -> None:
        dest = self.context.trash_dir / source
        if not self.dry_run:
            dest.parent.mkdir(exist_ok=True, parents=True)
            shutil.move(str(source), str(dest))
