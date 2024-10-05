# SPDX-FileCopyrightText: Copyright 2020-2024, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""
A set of metadata about this package.
Attributes correspond to [importlib.metadata] keys (see https://docs.python.org/3/library/importlib.metadata.html).

The metadata are loaded when this module is loaded and stored in the global [about][] for import.
The metadata is loaded dynamically by trying, in order:

1. Using `importlib.metadata(pkg)`, where `pkg` is this directory name.
2. Reading `<this_module_path>/../../../pyproject.toml` (logs with [logging.DEBUG][DEBUG]).
   If `project.readme` specifies a `file`, that file will be read and used as `description`.
   (It will `""` if no such file could be read.)
3. Falling back to `[]` , `{}`, or `""` for optional fields and [MISSING][] (`"??"`) for required fields.
   (logs with [logging.WARNING][WARNING]).

Please note that values loaded from `pyproject.toml` may differ from those loaded via importlib,
even though the `pyproject.toml` was used to build the package; this problem is unavoidable.
Regardless of which was used, the fields in `about` should be interpreted per importlib.

Any missing optional values will be `""`, `[]`, or `{}`.
"""

import logging
import tomllib
from dataclasses import asdict, dataclass, field
from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata as __importlib_load
from pathlib import Path
from typing import Literal, overload, Self

__all__ = ["About", "about", "root"]
__pkg = Path(__file__).parent.name
logger = logging.getLogger(__pkg)
_MISSING = ""  # value for missing required fields; must never be a real value
MISSING = _MISSING  # copy so that setting it has no (other) effect
# PyPi-recognized case-insensitive URL labels (https://docs.pypi.org/project_metadata/)
# the order of list elements matters slightly: the first will be preferred
_hyperlink_labels: dict[str, list[str]] = {
    "download": ["download"],
    "tracker": ["bug*", "issue*", "tracker*", "report*"],
    "changelog": ["changelog", "change log", "changes", "release notes", "news", "what's new", "history"],
    "docs": ["documentation*", "docs*"],
    "funding": ["funding", "sponsor*", "donation*", "donate*"],
}


@dataclass(frozen=True, slots=True, kw_only=True)
class About:
    """
    Metadata about this package (as in pip-installable / PyPi package).
    The values may be found via either [importlib.metadata][] (preferred) or `pyproject.toml`.
    Note that the fields with defaults are optional: The rest are required but can rarely be [MISSING][] (`"??"`).
    See this module's docstring for more info.

    Attributes:
        - meta_origin: **(required; always set)** the source of this metadata.
        - namespace: **(required; always set)** the name of the directory containing this module
          e.g. `mypkg` if the project name is `my-pkg`.
        - version: **(required; `MISSING` if not found)** importlib `Version`, or `project.version`.
        - name: **(required; `MISSING` if not found)** importlib `Name`, or `project.name`.
        - summary: **(required; `MISSING` if not found)** importlib `Summary`, or `project.description`.
        - license: **(required; `MISSING` if not found)** importlib `License`, or `project.license.text`;
          an SPDX license ID.
        - author: (optional; `""` if not found) importlib `Author`, or `name` from `project.authors`;
          e.g. `authors = [{"name": "Adam Addison", ...}, {"name": "Chloe Cho", ...}]`
          results in `Adam Addison and Chloe Cho`.
        - maintainer: (optional; `""` if not found) importlib `Author`, or `name` from `project.maintainers`.
        - description: (optional; `""` if not found) importlib `Description`, or the content of `project.readme.file`.
        - keywords: (optional; `[]` if not found)  importlib `Keywords`, or `project.keywords`.
        - homepage: (optional; `""` if not found) importlib `Home-page`, or `project.urls.Homepage`.
        - hyperlinks: (optional; `{}` if not found) importlib `Project-URL`, or `project.urls` (includes homepage);
          e.g. `{"Homepage": "https://github.com/org/abcd/"}`.
          The case of the keys is preserved, but lookups should be case-insensitive.
    """

    meta_origin: Literal["importlib", "pyproject", "none"]
    namespace: str
    version: str
    name: str
    summary: str
    license: str
    author: str = ""
    maintainer: str = ""
    description: str = ""
    keywords: list[str] = field(default_factory=list)  # JSON compat
    homepage: str = ""
    hyperlinks: dict[str, str] = field(default_factory=dict)

    @property
    def as_dict(self: Self) -> dict[str, str | list[str] | dict[str, str]]:
        """Returns this metadata set as a JSON-compatible dictionary."""
        return asdict(self)

    @property
    def docs_uri(self: Self) -> str:
        """Returns a hyperlink that PyPi recognizes for documentation; falls back to the homepage."""
        return self._get_standard_hyperlink("docs", self.homepage)

    @property
    def source_uri(self: Self) -> str:
        """Returns a hyperlink under the custom label `"source"`; falls back to the homepage."""
        return self._get_standard_hyperlink("source", self.homepage)

    @property
    def tracker_uri(self: Self) -> str:
        """Returns a hyperlink that PyPi recognizes for funding; falls back to the homepage."""
        return self._get_standard_hyperlink("tracker", self.homepage)

    @property
    def download_uri(self: Self) -> str:
        """Returns a hyperlink that PyPi recognizes for download; falls back to the homepage."""
        return self._get_standard_hyperlink("download", self.homepage)

    @property
    def changelog_uri(self: Self) -> str:
        """Returns a hyperlink that PyPi recognizes for changelog / release notes; falls back to the homepage."""
        return self._get_standard_hyperlink("changelog", self.homepage)

    @property
    def funding_uri(self: Self) -> str:
        """Returns a hyperlink that PyPi recognizes for funding; falls back to the homepage."""
        return self._get_standard_hyperlink("funding", self.homepage)

    @overload
    def find_hyperlink(self: Self, choices: list[str], fallback: str = "") -> str:
        return self.find_hyperlink(choices, fallback)

    def find_hyperlink(self: Self, choices: list[str], fallback: str | None = None) -> str | None:
        """
        Finds a hyperlink whose label matches one of the patterns in `choices`.
        Patterns are glob-like: `*` is recognized at the start and end.
        """
        links = {k.lower(): v for k, v in self.hyperlinks.items()}
        return About._get_matching_hyperlink(choices, links) or fallback

    def _get_standard_hyperlink(self: Self, label: str, fallback: str) -> str:
        if choices := _hyperlink_labels.get(label, []):
            links = {k.lower(): v for k, v in self.hyperlinks.items()}
            if v := About._get_matching_hyperlink(choices, links):
                return v
        return fallback

    @staticmethod
    def _get_matching_hyperlink(choices: list[str], links: dict[str, str]) -> str | None:
        for choice in choices:
            if value := About._test_matching_hyperlink(choice, links):
                return value
        return None

    @staticmethod
    def _test_matching_hyperlink(choice: str, links: dict[str, str]) -> str | None:
        if value := links.get(choice):
            return value
        # this is fast and avoids importing regex or glob
        for label, value in links.items():
            stripped_choice = choice.removesuffix("*").removeprefix("*")
            if (label == stripped_choice or choice.endswith("*") and label.startswith(stripped_choice)) and (
                label == stripped_choice or choice.startswith("*") and label.endswith(stripped_choice)
            ):
                return value
        return None


def _load_metadata(pkg: str, package_root: Path) -> About:  # nocov
    # 1: First, try `importlib`; will fail if our package is not installed
    data = _read_importlib(pkg)
    if data:
        return _about_importlib(data)
    # 2: Now try reading a pyproject.toml file
    pyproject_file = package_root / "pyproject.toml"
    data = _read_pyproject(pyproject_file, pkg)
    if data:
        readme = _read_readme(data, pyproject_file)
        return _about_pyproject(data, pkg, readme)
    return _about_empty(pkg)


def _read_importlib(pkg: str) -> dict[str, str | list[str]] | None:
    try:
        return __importlib_load(pkg).json
    except PackageNotFoundError:
        logger.debug(f"Did not find importlib metadata for package `{pkg}`. Is it installed?")
    return None


def _read_pyproject(pyproject_file: Path, pkg: str) -> dict | None:
    if pyproject_file.exists():
        try:
            data = tomllib.loads(pyproject_file.read_text(encoding="utf-8"))
            logger.debug(f"Using metadata for package `{pkg}` from `{pyproject_file}`.")
            return data
        except tomllib.TOMLDecodeError as e:
            logger.warning(f"Encountered error while decoding `{pyproject_file}`.", e)
    return None


def _read_readme(data: dict, pyproject_file: Path) -> str:
    filename = data.get("readme", {}).get("file", "")
    if filename:
        readme_file = pyproject_file.parent / filename
        try:
            return readme_file.read_text(encoding="utf-8")
        except OSError as e:
            logger.debug(f"Error reading `{readme_file}`.", e)
    return ""


def _about_importlib(data: dict[str, list[str] | str]) -> About:
    return About(
        meta_origin="importlib",
        namespace=__pkg,
        version=data.get("Version"),
        name=data.get("Name"),
        summary=data.get("Summary"),
        license=data.get("License"),
        author=data.get("Author", ""),
        maintainer=data.get("Maintainer", ""),
        description=data.get("Description", ""),
        keywords=data.get("Keywords", "").split(","),
        homepage=data.get("Home-page"),
        hyperlinks={s[: s.index(",")]: s[s.index(",") + 2 :] for s in data.get("Project-URL", [])},
    )


def _about_pyproject(data: dict, pkg: str, readme: str) -> About:
    proj = data.get("project", {})
    abt = About(
        meta_origin="pyproject",
        namespace=pkg,
        version=proj.get("version", _MISSING),
        name=proj.get("name", _MISSING),
        summary=proj.get("description", ""),  # yep, this is correct
        license=proj.get("license", {}).get("text", _MISSING),
        author=" and ".join([x.get("name", _MISSING) for x in proj.get("authors", [])]),
        maintainer=" and ".join([x.get("name", _MISSING) for x in proj.get("maintainers", [])]),
        description=readme,  # yep, this is correct, too
        keywords=proj.get("keywords", []),
        homepage=proj.get("urls", {}).get("Homepage", ""),
        hyperlinks=proj.get("urls"),
    )
    missing = {k for k, v in abt.as_dict.items() if v is None or v == _MISSING or len(v) == 0}
    logger.debug(f"Read metadata for package `{pkg}` from `pyproject.toml`. Missing {"; ".join(missing)}.")
    return abt


def _about_empty(pkg: str) -> About:
    return About(
        meta_origin="none",
        namespace=pkg,
        version=_MISSING,
        name=_MISSING,
        summary=_MISSING,
        license=_MISSING,
    )


root = Path(__file__).parent.parent.parent
about = _load_metadata(__pkg, root)
if __name__ == "__main__":
    print(about)
