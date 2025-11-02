# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""`tyranno new` command."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_NOTICE_FILE_TEMPLATE: Final = """
{{project.name}}
Copyright {{now_utc().year}}, Contributors to {{project.name}}

This product includes code written for Tyrannosaurus (Apache 2.0).
https://github.com/dmyersturnbull/tyrannosaurus
"""


@dataclass(frozen=True, kw_only=True, slots=True)
class New:
    """Project creator."""

    path: Path
    name: str
    license_id: str
    notice_file: bool

    def create(self) -> None:
        pass
