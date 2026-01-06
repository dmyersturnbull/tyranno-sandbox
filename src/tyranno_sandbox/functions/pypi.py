# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Custom JSONPath functions."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from niquests import Session

    from tyranno_sandbox._core import JsonBranch


@dataclass(frozen=True, slots=True)
class PypiFunctions:
    session: Session

    def extract_versions(self, pypi_data: JsonBranch) -> set[str]:
        versions: set[str] = set()
        for ver, files in pypi_data.get("releases", {}).items():
            if any(not f.get("yanked", False) for f in files):
                versions.add(ver)
        return versions

    def fetch_metadata(self, name: str) -> JsonBranch:
        url = f"https://pypi.org/pypi/{name}/json"
        # niquests `.json()` uses orjson if it's installed.
        response = self.session.get(url).raise_for_status()
        return response.json()
