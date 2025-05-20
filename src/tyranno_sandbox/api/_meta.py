# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Utils for server.
"""

from pathlib import Path
from typing import Final

from tyranno_sandbox._about import __about__ as about
from tyranno_sandbox._core import JsonBranch

__all__ = ["META"]

_description = None
if (p := Path("API.md")).exists():
    _description = p.read_text(encoding="utf-8")
# ::tyranno:: license_id = "$<<~.license.id>>"
_license_id = "Apache-2.0"
# ::tyranno:: license_name = "$<<~.license.name>>"
_license_name = "Apache License 2.0"
# ::tyranno:: license_uri = "$<<~.license.uri>>"
_license_uri = "https://spdx.org/licenses/Apache-2.0.html"

META: Final[JsonBranch] = {
    "title": about["name"],
    "summary": about["summary"],
    "description": _description,
    "version": about["version"],
    "license_info": {"name": _license_name, "identifier": _license_id, "url": _license_uri},
}
