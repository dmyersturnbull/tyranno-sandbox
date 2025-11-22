# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Project metadata.

This is a separate module so that it's easy to import.
For example, `mypkg/app.py` may want to write `"{__about__.name} (version v{__about__.version})"`,
while your `mypkg/__init__.py` includes lines like `from mypkg.app import Entry` for its public API.
(This would break if `mypkg.app` tried to `from mypkg import __about__`.)
"""

from collections.abc import Sequence
from typing import Final, NamedTuple, NotRequired, ReadOnly, Self, TypedDict, overload

__all__ = ["About", "UrlDict", "VersionParts", "__about__"]


class _FrozenList[T](Sequence[T]):
    def __init__(self, *items: T) -> None:
        super().__init__()
        self.__items = list(items)

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> Self: ...

    def __getitem__(self, index: int | slice) -> T | Self:
        result = self.__items[index]
        return type(self)(result) if isinstance(index, slice) else result

    def __len__(self) -> int:
        return len(self.__items)

    def __hash__(self) -> int:
        return hash(tuple(self.__items))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _FrozenList):
            return self.__items == other.__items
        return NotImplemented

    def __str__(self) -> str:
        return str(self.__items)


class UrlDict(TypedDict):
    """URLs for this project, [per PyPi](https://docs.pypi.org/project_metadata/).

    Names are from the `name` column, lowercased.
    `homepage`, `changelog`, and `source` are required.
    """

    homepage: ReadOnly[str]
    changelog: ReadOnly[str]
    source: ReadOnly[str]
    documentation: NotRequired[ReadOnly[str]]
    download: NotRequired[ReadOnly[str]]
    bug: NotRequired[ReadOnly[str]]
    funding: NotRequired[ReadOnly[str]]


class VersionParts(NamedTuple):
    """Major, minor, patch, and pre per semver.

    This project's versions conform to both PyPa (i.e. PEP 440) and SemVer rules.
    `pre` will normally be empty or `('alpha'|'beta'|'rc', nonnegative-int)`.
    """

    major: int
    minor: int
    patch: int
    pre: tuple[str | int, ...]

    @property
    def minor_version(self) -> str:
        return f"{self.major}.{self.minor}"

    @property
    def patch_version(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class About(TypedDict):
    # noinspection GrazieInspection
    """Metadata about this package.

    Attributes:
        namespace: name of the directory containing this module.
        name: pyproject `project.name`                   / importlib `Name`    .
        version: pyproject `project.version`             / importlib `version`.
        version_parts: (parsed `version`)
        summary: pyproject `project.description`         / importlib `Summary`.
        license: pyproject `project.license.text`        / importlib `License`;
          an SPDX ID such as `Apache-2.0`.
        authors: pyproject `project.authors[*].name`     / importlib `Author` split by ` and `;
          e.g. `["Kerri Kerrigan", "Adam Addison"]`.
        maintainers: pyproject `project.authors[*].name` / importlib `Author` split by ` and `;
          e.g. `["Kerri Kerrigan", "Adam Addison"]`.
        keywords: pyproject `project.keywords`           / importlib `Keywords`.
        urls: pyproject  `project.urls` subset           / `Project-URL` subset.
          Only recognized general URLs from
          [PyPi Project Metadata](https://docs.pypi.org/project_metadata/).
          Attributes are lowercased versions of the "Name", from the "General URL" table.
    """

    name: ReadOnly[str]
    namespace: ReadOnly[str]
    vendor: ReadOnly[str]
    version: ReadOnly[str]
    version_parts: ReadOnly[VersionParts]
    summary: ReadOnly[str]
    license: ReadOnly[str]
    authors: ReadOnly[Sequence[str]]
    maintainers: ReadOnly[Sequence[str]]
    keywords: ReadOnly[Sequence[str]]
    urls: ReadOnly[UrlDict]


__about__: Final = About(
    # ::tyranno:: name="$<<~.namespace>>",
    namespace="tyranno_sandbox",
    # ::tyranno:: name="$<<~.vendor>>",
    vendor="dmyersturnbull",
    # ::tyranno:: name="$<<project.name>>",
    name="tyranno-sandbox",
    # ::tyranno:: version="$<<project.version>>",
    version="0.0.1-alpha.0",
    # ::tyranno:: version="$<<project.version.semver(@).py_tuple(@)>>",
    version_parts=VersionParts(0, 0, 1, ("alpha", 0)),
    # ::tyranno:: summary="$<<project.summary>>",
    summary="Sandbox to test CI/CD in Tyrannosaurus",
    # ::tyranno:: authors=$<<project.authors[*].name>>,
    authors=_FrozenList("Douglas Myers-Turnbull"),
    # ::tyranno:: maintainers=$<<project.maintainers[*].name>>,
    maintainers=_FrozenList("Douglas Myers-Turnbull"),
    # ::tyranno:: name=$<<project.keywords>>,
    keywords=_FrozenList(
        "ci/cd", "cookiecutter", "github-workflow", "pyproject", "python-template"
    ),
    # ::tyranno:: license="$<<project.license.text>>",
    license="Apache-2.0",
    urls=UrlDict(
        # ::tyranno:: homepage="$<<project.urls.Homepage>>",
        homepage="https://github.com/dmyersturnbull/tyranno-sandbox",
        # ::tyranno:: source="$<<project.urls.Source>>",
        source="https://github.com/dmyersturnbull/tyranno-sandbox",
        # ::tyranno:: documentation="$<<project.urls.Documentation>>",
        documentation="https://github.com/dmyersturnbull/tyranno-sandbox",
        # ::tyranno:: changelog="$<<project.urls."Release Notes">>",
        changelog="https://github.com/dmyersturnbull/tyranno-sandbox/releases",
        # ::tyranno:: download="$<<project.urls.Download>>",
        download="https://pypi.org/project/tyranno-sandbox/",
        # ::tyranno:: bug="$<<project.urls.Tracker>>",
        bug="https://github.com/dmyersturnbull/tyranno-sandbox/issues",
    ),
)


if __name__ == "__main__":
    print(__about__)  # noqa: T201
