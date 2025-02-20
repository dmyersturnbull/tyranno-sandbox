# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
""" """

import math
from datetime import datetime
from operator import itemgetter
from typing import Any
from zoneinfo import ZoneInfo

import niquests
from jmespath import functions
from packaging.version import Version
from packaging.specifiers import SpecifierSet


def _format_dt(dt: datetime, *, sep: str = "T", ts: str = "seconds") -> str:
    stamp = dt.isoformat(sep, ts)
    # Don't replace +00:00 with Z for Europe/London (canonical), Europe/Jersey, etc.
    if dt.tzname().removeprefix("Etc/") in {"UTC", "Zulu", "UCT", "GMT", "Greenwich", "Universal"}:
        # I couldn't confirm that Python never uses -00:00, which RFC-3339 supports.
        # ISO 8601 inexplicably supports ±, but let's not check that.
        stamp = stamp.replace("+00:00", "Z").replace("-00:00", "Z")
    return stamp


def _datetime_to_dict(dt: datetime) -> dict[str, str | int]:
    raw = _format_dt(dt, ts="microseconds")
    stamp_z = _format_dt(dt)
    formatted = _format_dt(dt, sep=" ")
    # starting at 1
    week_of_month = int(math.ceil(dt.day + dt.replace(day=1).weekday() / 7))
    even_week = week_of_month % 2 == 0
    return {
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
        "raw-string": raw,
        "formatted": formatted,
        "iso-8601": stamp_z,
        "rfc-3339": stamp_z,
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%H:%M:%S"),
        "raw-time": dt.strftime("%H:%M:%S:%ffffff"),
        "week-parity": "even" if even_week else "odd",
        "unix-time": str(int(dt.timestamp())),
    }


NOW_LOCAL = datetime.now().astimezone()
NOW_UTC = NOW_LOCAL.astimezone(ZoneInfo("Etc/UTC"))
LOCAL_TIME_DICT = _datetime_to_dict(NOW_LOCAL)
UTC_TIME_DICT = _datetime_to_dict(NOW_UTC)


def _dl_license(spdx_id: str) -> dict[str, Any]:
    url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/details/" + spdx_id + ".json"
    return niquests.get(url).raise_for_status().json()


def _get_license_uris(data: dict[str, Any]) -> list[str]:
    urls = (u for u in data["crossRef"] if u.get("isValid") and u.get("isLive"))
    urls = sorted(urls, key=itemgetter("order"))
    # noinspection HttpUrlsUsage
    return [u["url"].replace("http://", "https://") for u in urls]


def _dl_pypi_metadata(name: str):
    url = f"https://pypi.org/pypi/${name}/json"
    # niquests `.json()` uses orjson if it's installed.
    return niquests.get(url).raise_for_status().json()


def _sanitize_pep440(v: Version | str) -> str:
    if isinstance(v, str):
        v = Version(v)
    epoch = f"{v.epoch}::" if v.epoch else ""
    main = f"{v.major}.{v.minor}.{v.micro}"
    pre = f"-{v.pre}" if v.pre else ""
    dev = f".dev{v.dev}" if v.dev else ""
    post = f".post{v.post}" if v.post else ""
    return epoch + main + pre + dev + post


class TyrannoFunctions(functions.Functions):
    @functions.signature({"types": ["list", "string"]})
    def _func_filter_pep440_by_specifier(self, versions: list[str], specifier: str) -> list[str]:
        return [_sanitize_pep440(v) for v in versions if Version(v) in SpecifierSet(specifier)]

    @functions.signature({"types": ["list"]})
    def _func_max_pep440(self, versions: list[str] | str) -> str:
        return _sanitize_pep440(max(Version(v) for v in versions))

    @functions.signature({"types": ["list"]})
    def _func_min_pep440(self, versions: list[str] | str) -> str:
        return _sanitize_pep440(min(Version(v) for v in versions))

    @functions.signature({"types": ["string"]})
    def _func_parse_pep440(self, pep440_string: str) -> dict[str, int | str]:
        v = Version(pep440_string)
        return {
            "epoch": v.epoch,
            "major": v.major,
            "minor": v.minor,
            "patch": v.micro,  # semver equivalent
            "micro": v.micro,
            "pre": f"{v.pre[0]}{v.pre[1]}" if v.pre else "",
            "dev": str(v.dev) if v.dev else "",
            "post": str(v.post) if v.post else "",
            "string": _sanitize_pep440(v),
        }

    @functions.signature({"types": ["string"]})
    def _func_spdx_license(self, spdx_id: str) -> dict[str, str]:
        data = _dl_license(spdx_id)
        uris = _get_license_uris(data)
        return {
            "id": spdx_id,
            "spdx-id": spdx_id,
            "name": data["name"],
            "uri": f"https://spdx.org/licenses/${spdx_id}.html",
            "uris": uris,
            "header": f"SPDX-License-Identifier: ${spdx_id}",
            "text": data["licenseText"],
        }

    @functions.signature({"types": ["string"]})
    def _func_utc_datetime(self) -> dict[str, str | int]:
        return UTC_TIME_DICT

    @functions.signature({"types": ["dict"]})
    def _func_pypi_data(self, package_name: str) -> dict[str, Any]:
        return _dl_pypi_metadata(package_name)
