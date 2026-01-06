# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Custom JSONPath functions."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Final

from packaging.specifiers import SpecifierSet
from packaging.version import Version as Pep440
from semver import VersionInfo as Semver

from tyranno_sandbox._global_vars import STARTUP
from tyranno_sandbox.functions.licenses import LicenseDict, LicenseFunctions
from tyranno_sandbox.functions.pep440 import Pep440Dict, Pep440Functions
from tyranno_sandbox.functions.pypi import PypiFunctions
from tyranno_sandbox.functions.semver import SemverDict, SemverFunctions
from tyranno_sandbox.functions.times import DatetimeFunctions, TimeDict

if TYPE_CHECKING:
    from niquests import Session


class Functions:
    def __init__(self, session: Session) -> None:
        self._f_time = DatetimeFunctions()
        self._f_license = LicenseFunctions(session)
        self._f_pep440 = Pep440Functions()
        self._f_pypi = PypiFunctions(session)
        self._f_semver = SemverFunctions()
        self._now_local: Final = self._f_time.of(STARTUP.local)
        self._now_utc: Final = self._f_time.of(STARTUP.utc)

    def semver(self, semver_string: str) -> SemverDict:
        return self._f_semver.of(semver_string)

    def semver_ascending(self, versions: list[str]) -> list[str]:
        sorted_ = sorted(Semver.parse(v) for v in versions)
        return [str(p) for p in sorted_]

    def semver_descending(self, versions: list[str]) -> list[str]:
        sorted_ = sorted((Semver.parse(v) for v in versions), reverse=True)
        return [str(p) for p in sorted_]

    def semver_max(self, versions: list[str]) -> str:
        return str(max(Semver.parse(v) for v in versions))

    def semver_min(self, versions: list[str]) -> str:
        return str(min(Semver.parse(v) for v in versions))

    def pep440(self, pep440_string: str) -> Pep440Dict:
        return self._f_pep440.of(pep440_string)

    def pep440_filter(self, versions: list[str], predicate: str) -> list[str]:
        return [
            self._f_pep440.sanitize(v) for v in versions if Pep440(v) in SpecifierSet(predicate)
        ]

    def pep440_find_for_spec(self, spec: str) -> list[str]:
        pkg, predicate = self._f_pep440.split_spec(spec)
        versions = self.pypi_versions(pkg)
        return self.pep440_filter(list(versions), predicate)

    def pep440_ascending(self, versions: list[str]) -> list[str]:
        sorted_ = sorted(Pep440(v) for v in versions)
        return [self._f_pep440.sanitize(p) for p in sorted_]

    def pep440_descending(self, versions: list[str]) -> list[str]:
        sorted_ = sorted((Pep440(v) for v in versions), reverse=True)
        return [self._f_pep440.sanitize(p) for p in sorted_]

    def pep440_max(self, versions: list[str]) -> str:
        return self._f_pep440.sanitize(max(Pep440(v) for v in versions))

    def pep440_min(self, versions: list[str]) -> str:
        return self._f_pep440.sanitize(min(Pep440(v) for v in versions))

    def pep440_max_per(self, versions: list[str], per: str) -> list[str]:
        return self._f_pep440.max_per(versions, per)

    def pypi_versions(self, pkg: str) -> set[str]:
        return self._f_pypi.extract_versions(self._f_pypi.fetch_metadata(pkg))

    def spdx_license(self, spdx_id: str) -> LicenseDict:
        return self._f_license.license_data(spdx_id)

    def timestamp(self, ts: str) -> TimeDict:
        return self._f_time.of(datetime.fromisoformat(ts))

    def now_local(self) -> TimeDict:
        return self._now_local

    def now_utc(self) -> TimeDict:
        return self._now_utc

    def pypi_data(self, package_name: str) -> dict[str, Any]:
        return self._f_pypi.fetch_metadata(package_name)
