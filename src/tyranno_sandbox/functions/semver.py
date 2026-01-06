# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from semver import VersionInfo as Semver

from tyranno_sandbox.functions._core import FunctionError


class SemverDict(TypedDict):
    full_version: str
    public_version: str
    minor_version: str
    patch_version: str
    major: int
    minor: int
    patch: int
    pre: str
    pre_ids: list[str]
    build: str


class NpmSpecDict(TypedDict):
    package: str
    predicate: str


@dataclass(frozen=True, slots=True)
class SemverFunctions:
    def of(self, v: Semver | str) -> SemverDict:
        if isinstance(v, str):
            v = Semver.parse(v)
        pre = v.prerelease or ""
        return SemverDict(
            full_version=str(v),
            public_version=str(Semver(v.major, v.minor, v.patch, v.prerelease)),
            minor_version=f"{v.major}.{v.minor}",
            patch_version=str(v.finalize_version()),
            major=v.major,
            minor=v.minor,
            patch=v.patch,
            pre=pre,
            pre_ids=pre.split("."),
            build=v.build,
        )

    def max_per(self, versions: list[str], per: str) -> list[str]:
        versions = [Semver.parse(v) for v in versions]
        options = {"major", "minor", "patch"}
        if per not in options:
            msg = f"Argument '{per}' is not one of {options}."
            raise FunctionError.from_call(msg, depth=1)
        best = {}
        for v in versions:
            v0 = getattr(v, per)
            if v0 not in best or v > best[v0]:
                best[v0] = v
        return [str(b) for b in best.values()]
