# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""
Tyrannosaurus project metadata.

This is a separate module so that it's easy to import.
For example, your `mypkg/app.py` may want to write `f"{__about__.name} (version v${__about__.version})"`,
while your `mypkg/__init__.py` includes lines like `from mypkg.app import Entry` for its public API.
(This would break if `mypkg.app` tried to `from mypkg import __about__`.)
"""

from dataclasses import dataclass, asdict
from typing import Self


@dataclass(frozen=True, slots=True, kw_only=True)
class UrlDict:
    """URLs for this project, per [https://docs.pypi.org/project_metadata/]."""

    homepage: str
    changelog: str
    source: str
    documentation: str | None = None
    download: str | None = None
    bug: str | None = None
    funding: str | None = None

    @property
    def as_dict(self: Self) -> dict[str, str | list[str] | dict[str, str]]:
        """Returns a JSON-compatible dictionary."""
        return asdict(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class About:
    """
    Metadata about this package.

    Attributes:
        namespace:   name of the directory containing this module.
        name:        pyproject `project.name`            / importlib `Name`    .
        version:     pyproject `project.version`         / importlib `version`.
        summary:     pyproject `project.description`     / importlib `Summary`.
        license:     pyproject `project.license.text`    / importlib `License`;
            an SPDX ID such as `Apache-2.0`.
        authors:     pyproject `project.authors[*].name` / importlib `Author` split by ` and `;
            e.g. `["Kerri Kerrigan", "Adam Addison"]`.
        maintainers: pyproject `project.authors[*].name` / importlib `Author` split by ` and `;
            e.g. `["Kerri Kerrigan", "Adam Addison"]`.
        keywords:  pyproject `project.keywords`          / importlib `Keywords`.
        urls:        pyproject  `project.urls` subset    / `Project-URL` subset.
            Only recognized general URLs from [PyPi Project Metadata](https://docs.pypi.org/project_metadata/).
            Attributes are lowercased versions of the "Name", from the "General URL" table.
    """

    name: str
    namespace: str
    version: str
    summary: str
    license: str
    authors: list[str]
    maintainers: list[str]
    keywords: list[str]
    urls: UrlDict

    @property
    def as_dict(self: Self) -> dict[str, str | list[str] | dict[str, str]]:
        """Returns a JSON-compatible dictionary."""
        return asdict(self)


__about__ = About(
    namespace="tyranno",
    # :tyranno: name="${project.name}",
    name="sandbox-tyranno",
    # :tyranno: version="${project.version}",
    version="0.0.1-alpha0",
    # :tyranno: summary="${project.summary}",
    summary="Sandbox to test CI/CD in Tyrannosaurus",
    # :tyranno: authors=${project.authors[*].name},
    authors=["Douglas Myers-Turnbull"],
    # :tyranno: maintainers=${project.maintainers[*].name},
    maintainers=["Douglas Myers-Turnbull"],
    # :tyranno: name=${project.keywords},
    keywords=["python", "ci", "cd"],
    # :tyranno: license="${project.license.text}",
    license="Apache-2.0",
    urls=UrlDict(
        # :tyranno: homepage="${project.urls.Homepage}",
        homepage="https://github.com/dmyersturnbull/cicd",
        # :tyranno: source="${project.urls.Source}",
        source="https://github.com/dmyersturnbull/cicd",
        # :tyranno: documentation="${project.urls.Documentation}",
        documentation="https://github.com/dmyersturnbull/cicd",
        # :tyranno: changelog="${project.urls.Release Notes}",
        changelog="https://github.com/dmyersturnbull/cicd/releases",
        # :tyranno: download="${project.urls.Download}",
        download="https://pypi.org/project/cicd/",
        # :tyranno: bug="${project.urls.Tracker}",
        bug="https://github.com/dmyersturnbull/cicd/issues",
    ),
)
