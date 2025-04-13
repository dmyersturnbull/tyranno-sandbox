# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
JMESPath utilities.
"""

# ruff: noqa: UP013, PIE804  # We'll use the `**{}` style for consistency.
from __future__ import annotations

import math
from datetime import datetime
from operator import itemgetter
from typing import Any, Final, TypedDict

import niquests
from jmespath import functions
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from tyranno_sandbox._global_vars import STARTUP

__all__ = ["TyrannoJmesFunctions"]

LicenseDict = TypedDict(
    "LicenseDict", {"id": str, "spdx-id": str, "name": str, "uri": str, "uris": list[str], "header": str, "text": str}
)

Pep440Dict = TypedDict(
    "Pep440Dict",
    {
        "string": str,
        "epoch": int,
        "major": int,
        "minor": int,
        "patch": int,
        "micro": int,
        "pre": str,
        "dev": str,
        "post": str,
    },
)
SemverDict = TypedDict(
    "SemverDict", {"string": str, "major": int, "minor": int, "patch": int, "pre": str, "build": str}
)

TimestampDict = TypedDict(
    "TimestampDict",
    {
        "year": int,
        "month": int,
        "day": int,
        "hour": int,
        "minute": int,
        "second": int,
        "microsecond": int,
        "utc-offset": str | None,
        "zone": str | None,
        "is-dst": bool,
        "raw-string": str,
        "formatted": str,
        "iso-8601": str,
        "rfc-3339": str,
        "date": str,
        "time": str,
        "raw-time": str,
        "week-parity": str,
        "unix-time": str,
    },
)


class _Utils:
    """Internal utilities used by custom JMESPath functions."""

    @staticmethod
    def pep440_info(v: Version) -> Pep440Dict:
        return Pep440Dict(
            **{
                "string": _Utils.sanitize_pep440(v),
                "epoch": v.epoch,
                "major": v.major,
                "minor": v.minor,
                "patch": v.micro,
                "micro": v.micro,
                "pre": f"{v.pre[0]}{v.pre[1]}" if v.pre else "",
                "dev": str(v.dev) if v.dev else "",
                "post": str(v.post) if v.post else "",
            }
        )

    @staticmethod
    def format_dt(dt: datetime, *, sep: str = "T", ts: str = "seconds") -> str:
        stamp = dt.isoformat(sep, ts)
        # Don't replace +00:00 with Z for Europe/London (canonical), Europe/Jersey, etc.
        if dt.tzname().removeprefix("Etc/") in {"UTC", "Zulu", "UCT", "GMT", "Greenwich", "Universal"}:
            # I couldn't confirm that Python never uses -00:00, which RFC-3339 supports.
            # ISO 8601 inexplicably supports ±, but let's not check that.
            stamp = stamp.replace("+00:00", "Z").replace("-00:00", "Z")
        return stamp

    @staticmethod
    def datetime_to_dict(dt: datetime) -> TimestampDict:
        # starting at 1
        week_of_month: int = math.ceil(dt.day + dt.replace(day=1).weekday() / 7)
        even_week = week_of_month % 2 == 0
        return TimestampDict(
            **{
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
                "second": dt.second,
                "microsecond": dt.microsecond,
                "utc-offset": dt.utcoffset(),
                "zone": dt.tzname(),
                "is-dst": dt.dst() is not None and dt.dst() != 0,
                "raw-string": _Utils.format_dt(dt, ts="microseconds"),
                "formatted": _Utils.format_dt(dt, sep=" "),
                "iso-8601": _Utils.format_dt(dt),
                "rfc-3339": _Utils.format_dt(dt),
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M:%S"),
                "raw-time": dt.strftime("%H:%M:%S:%ffffff"),
                "week-parity": "even" if even_week else "odd",
                "unix-time": str(int(dt.timestamp())),
            }
        )

    @staticmethod
    def license_data(spdx_id: str) -> LicenseDict:
        data = _Utils._dl_license(spdx_id)
        uris = _Utils._get_license_uris(data)
        return LicenseDict(
            **{
                "id": spdx_id,
                "spdx-id": spdx_id,
                "name": data["name"],
                "uri": f"https://spdx.org/licenses/{spdx_id}.html",
                "uris": uris,
                "header": f"SPDX-License-Identifier: ${spdx_id}",
                "text": data["licenseText"],
            }
        )

    @staticmethod
    def _dl_license(spdx_id: str) -> dict[str, Any]:
        url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/details/" + spdx_id + ".json"
        return niquests.get(url).raise_for_status().json()

    @staticmethod
    def _get_license_uris(data: dict[str, Any]) -> list[str]:
        urls = (u for u in data["crossRef"] if u.get("isValid") and u.get("isLive"))
        urls = sorted(urls, key=itemgetter("order"))
        # noinspection HttpUrlsUsage
        return [u["url"].replace("http://", "https://") for u in urls]

    @staticmethod
    def dl_pypi_metadata(name: str) -> dict[str, Any]:
        url = f"https://pypi.org/pypi/{name}/json"
        # niquests `.json()` uses orjson if it's installed.
        return niquests.get(url).raise_for_status().json()

    @staticmethod
    def sanitize_pep440(v: Version | str) -> str:
        if isinstance(v, str):
            v = Version(v)
        epoch = f"{v.epoch}::" if v.epoch else ""
        main = f"{v.major}.{v.minor}.{v.micro}"
        pre = f"-{v.pre}" if v.pre else ""
        dev = f".dev{v.dev}" if v.dev else ""
        post = f".post{v.post}" if v.post else ""
        return epoch + main + pre + dev + post


_UTC_TIME_DICT: Final[TimestampDict] = _Utils.datetime_to_dict(STARTUP.utc)
_LOCAL_TIME_DICT: Final[TimestampDict] = _Utils.datetime_to_dict(STARTUP.local)


class TyrannoJmesFunctions(functions.Functions):
    """Collection of custom JMESPath functions."""

    @functions.signature({"types": ["list", "string"]})
    def _func_pep440_filter_by_spec(self, versions: list[str], specifier: str) -> list[str]:
        return [_Utils.sanitize_pep440(v) for v in versions if Version(v) in SpecifierSet(specifier)]

    @functions.signature({"types": ["list"]})
    def _func_pep440_max(self, versions: list[str]) -> str:
        return _Utils.sanitize_pep440(max(Version(v) for v in versions))

    @functions.signature({"types": ["list"]})
    def _func_pep440_min(self, versions: list[str]) -> str:
        return _Utils.sanitize_pep440(min(Version(v) for v in versions))

    @functions.signature({"types": ["string"]})
    def _func_pep440_parse(self, pep440_string: str) -> Pep440Dict:
        return _Utils.pep440_info(Version(pep440_string))

    @functions.signature({"types": ["string"]})
    def _func_spdx_license(self, spdx_id: str) -> LicenseDict:
        return _Utils.license_data(spdx_id)

    @functions.signature({"types": ["string"]})
    def _func_utc_datetime(self) -> dict[str, str | int]:
        return _UTC_TIME_DICT

    @functions.signature({"types": ["dict"]})
    def _func_pypi_data(self, package_name: str) -> dict[str, Any]:
        return _Utils.dl_pypi_metadata(package_name)
