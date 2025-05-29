# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Custom JMESPath functions."""

from __future__ import annotations

import calendar
import inspect
import math
import re
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from operator import itemgetter
from typing import TYPE_CHECKING, Any, Final, Literal, NamedTuple, Self, TypedDict, override

from niquests import Session
from packaging.specifiers import SpecifierSet
from packaging.version import Version as Pep440
from semver import VersionInfo as Semver

from tyranno_sandbox._global_vars import STARTUP

__all__ = ["TyrannoJmesFunctions"]


if TYPE_CHECKING:
    from types import FrameType, TracebackType

    from tyranno_sandbox._core import Json


class CallerInfo(NamedTuple):
    """The name and args of a calling function."""

    name: str
    args: dict[str, Any]


def get_caller_info(depth: int) -> CallerInfo:
    """Finds the function name and args for the caller (for `depth == 1`), etc."""
    this_frame = inspect.currentframe()
    if not this_frame:
        msg = "Current frame is unavailable."
        raise AssertionError(msg)
    frame: FrameType = this_frame
    for i in range(depth + 1):  # + 1 for this function
        if not frame.f_back:
            msg = f"Caller of frame {frame} (depth {i} from {this_frame}) is unavailable."
            raise AssertionError(msg)
        frame = frame.f_back
    return CallerInfo(frame.f_code.co_name, {**frame.f_locals})


class DateTuple(NamedTuple):
    year: int
    month: int
    day: int


class TimeTuple(NamedTuple):
    hour: int
    minute: int
    second: int
    microsecond: int


class LicenseDict(TypedDict):
    id: str
    spdx_id: str
    name: str
    uri: str
    links: list[str]
    header: str
    text: str


class Pep440Dict(TypedDict):
    full_version: str
    normalized_version: str
    public_version: str
    major_version: str
    minor_version: str
    micro_version: str
    epoch: int
    major: int
    minor: int
    micro: int
    patch: int
    pre: str
    dev: str
    post: str
    pre_type: str  # `""` if none
    pre_number: int | Literal[""]
    dev_number: int | Literal[""]
    post_number: int | Literal[""]


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


class Pep440SpecDict(TypedDict):
    package: str
    predicate: str


class NpmSpecDict(TypedDict):
    package: str
    predicate: str


class DatetimeDict(TypedDict):
    rfc_9557: str
    rfc_9557_utc: str
    rfc_3339: str
    rfc_3339_utc: str
    iso_8601_week_date: str
    unix_time: int
    formatted_local: str
    formatted: str
    date: str
    date_tuple: DateTuple
    time: str
    truncated_time: str
    time_tuple: TimeTuple
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    microsecond: int
    offset: str
    zone: str
    is_dst: bool
    is_leap_year: bool
    month_name: str
    month_abbr: str
    week_number: int
    week_parity: int
    day_name: str
    day_abbr: str
    day_number: int


class DurationDict(TypedDict):
    string: str
    iso_8601_hms: str
    iso_8601_dhms: str
    hms: str
    days: float
    hours: float
    minutes: float
    seconds: float
    microseconds: int
    day_part: int
    second_part: int
    microsecond_part: int


@dataclass(frozen=True, slots=True, kw_only=True)
class JmesFunctionError(Exception):
    """An error in fetching data from e.g. PyPi."""

    function: str
    args: dict[str, Any]
    message: str

    @classmethod
    def from_call(cls, message: str, *, depth: int) -> JmesFunctionError:
        name, args = get_caller_info(depth)
        return JmesFunctionError(function=name, args=args, message=message)

    def __str__(self) -> str:
        return f"Error in {self.function} with args {self.args}: {self.message}"


class _Utils(AbstractContextManager):
    """Internal utilities used by custom JMESPath functions."""

    def __init__(self) -> None:
        self.__session = Session()

    @override
    def __enter__(self) -> Self:
        self.__session.__enter__()
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.__session.__exit__(exc_type, exc_val, exc_tb)

    # IANA timezones that are aliases for Etc/UTC.
    UTC_NAMES: Final[frozenset[str]] = frozenset(
        {"Etc/UTC", "Etc/Universal", "Etc/UCT", "Etc/Zulu"}
    )
    PEP440_PRE_STRS: Final[dict[str, str]] = {
        "alpha": "a",
        "beta": "b",
        "c": "rc",
        "pre": "rc",
        "preview": "rc",
    }
    PEP440_SPEC_RE: Final[re.Pattern] = re.compile(r"""([A-Za-z0-9_-]++)(.++)""")

    def pep440_info(self, v: Pep440) -> Pep440Dict:
        major_vr = f"{v.epoch}!{v.major}" if v.epoch else str(v.major)
        minor_vr = f"{major_vr}.{v.minor}"
        return Pep440Dict(
            full_version=self.sanitize_pep440(v),
            normalized_version=self.normalize_pep440(v),
            public_version=v.public,
            major_version=major_vr,
            minor_version=minor_vr,
            micro_version=v.base_version,
            epoch=v.epoch,
            major=v.major,
            minor=v.minor,
            patch=v.micro,
            micro=v.micro,
            pre=f"{v.pre[0]}{v.pre[1]}" if v.pre is not None else "",
            dev=f"dev{v.dev}" if v.dev is not None else "",
            post=f"post{v.post}" if v.post is not None else "",
            pre_type=v.pre[0] if v.pre is not None else "",
            pre_number=v.pre[1] if v.pre is not None else "",
            dev_number=v.dev if v.dev is not None else "",
            post_number=v.post if v.post is not None else "",
        )

    def semver_info(self, v: Semver) -> SemverDict:
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

    def format_dt(self, dt: datetime, *, sep: str = "T", ts: str = "microseconds") -> str:
        if dt.tzname() is None:
            msg = f"Datetime instance {dt} is not zoned."
            raise JmesFunctionError.from_call(msg, depth=2)
        stamp = dt.isoformat(sep, ts)
        # Don't replace +00:00 with Z for Europe/London (canonical), Europe/Jersey, etc.
        if dt.tzname().removeprefix("Etc/") in _Utils.UTC_NAMES:
            # I couldn't confirm that Python never uses -00:00, which RFC 3339 supports.
            # ISO 8601 inexplicably supports ±, but let's not check that.
            stamp = stamp.replace("+00:00", "Z").replace("-00:00", "Z")
        return stamp

    def datetime_to_dict(self, dt: datetime) -> DatetimeDict:
        # starting at 1
        week_of_month: int = math.ceil(dt.day + dt.replace(day=1).weekday() / 7)
        rfc_9557 = self.format_dt(dt) + (f"[{dt.tzname()}]" if dt.tzname() else "")
        return DatetimeDict(
            rfc_9557=rfc_9557,
            rfc_9557_utc=self.format_dt(dt.astimezone(UTC)) + "[Etc/UTC]",
            rfc_3339=self.format_dt(dt),
            rfc_3339_utc=self.format_dt(dt.astimezone(UTC)),
            iso_8601_week_date=dt.strftime("%G-W%V-%u"),
            unix_time=int(dt.timestamp()),
            formatted_local=dt.strftime("%Y-%m-%d %H:%M:%S"),
            formatted=self.format_dt(dt, sep=" ", ts="seconds"),
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            microsecond=dt.microsecond,
            offset=dt.strftime("%z"),
            zone=dt.tzname(),
            is_dst=dt.dst() not in {None, 0},
            date=dt.strftime("%Y-%m-%d"),
            date_tuple=DateTuple(dt.year, dt.month, dt.day),
            time=dt.strftime("%H:%M:%S:%ffffff"),
            truncated_time=dt.strftime("%H:%M:%S"),
            time_tuple=TimeTuple(dt.hour, dt.minute, dt.second, dt.microsecond),
            day_number=dt.weekday(),
            day_name=dt.strftime("%A"),
            day_abbr=dt.strftime("%a"),
            month_name=dt.strftime("%B"),
            month_abbr=dt.strftime("%b"),
            week_number=dt.isocalendar().week,
            week_parity=week_of_month % 2,
            is_leap_year=calendar.isleap(dt.year),
        )

    def license_data(self, spdx_id: str) -> LicenseDict:
        data = self._dl_license(spdx_id)
        uris = self._get_license_uris(data)
        return LicenseDict(
            id=spdx_id,
            spdx_id=spdx_id,
            name=data["name"],
            uri=f"https://spdx.org/licenses/{spdx_id}.html",
            links=uris,
            header=f"SPDX-License-Identifier: {spdx_id}",
            text=data["licenseText"],
        )

    def _dl_license(self, spdx_id: str) -> dict[str, Any]:
        dir_ = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/details"
        url = f"{dir_}/{spdx_id}.json"
        return self.__session.get(url).raise_for_status().json()

    def _get_license_uris(self, data: Json) -> list[str]:
        urls = (u for u in data["crossRef"] if u.get("isValid") and u.get("isLive"))
        urls = sorted(urls, key=itemgetter("order"))
        # noinspection HttpUrlsUsage
        return [u["url"].replace("http://", "https://") for u in urls]

    def extract_pypi_versions(self, pypi_data: Json) -> set[str]:
        versions = set()
        for vr, files in pypi_data.get("releases", {}).items():
            if any(not f.get("yanked", False) for f in files):
                versions.add(vr)
        return versions

    def dl_pypi_metadata(self, name: str) -> Json:
        url = f"https://pypi.org/pypi/{name}/json"
        # niquests `.json()` uses orjson if it's installed.
        return self.__session.get(url).raise_for_status().json()

    def split_pep440_spec(self, spec: str) -> tuple[str, str]:
        if m := self.PEP440_SPEC_RE.fullmatch(spec):
            return m.group(1), m.group(2)
        raise ValueError(spec)

    def sanitize_pep440(self, v: Pep440 | str) -> str:
        if isinstance(v, str):
            v = Pep440(v)
        has_pre = v.pre is not None
        has_post = v.post is not None
        has_dev = v.dev is not None
        if sum((has_pre, has_post, has_dev)):
            msg = f"PyPa package version {v} mixes pre, post, and/or dev numbers."
            raise JmesFunctionError.from_call(msg, depth=2)
        epoch = f"{v.epoch}!" if v.epoch else ""
        main = f"{v.major}.{v.minor}.{v.micro}"
        pre = f"-{v.pre[0]}{v.pre[1]}" if has_pre else ""
        dev = f"-dev{v.dev}" if has_dev else ""
        post = f"-post{v.post}" if has_post else ""
        return epoch + main + pre + dev + post

    def normalize_pep440(self, v: Pep440 | str, *, force_epoch: bool = False) -> str:
        if isinstance(v, str):
            v = Pep440(v)
        has_pre = v.pre is not None
        has_post = v.post is not None
        has_dev = v.dev is not None
        main = f"{v.major}.{v.minor}.{v.micro}"
        epoch = f"{v.epoch}!" if v.epoch or force_epoch else ""
        if has_pre and v.pre[0] not in self.PEP440_PRE_STRS:
            msg = f"PyPa package version {v} has an unrecognized prerelease type {v.pre[0]}."
            raise JmesFunctionError.from_call(msg, depth=2)
        # The normal-form separators are '' for pre, '-' for dev, and '-' for post.
        pre = self.PEP440_PRE_STRS[v.pre[0]] + str(v.pre[1]) if has_pre else ""
        post = f".post{v.post}" if has_post else ""
        dev = f".dev{v.dev}" if has_dev else ""
        return epoch + main + pre + dev + post


U: Final[_Utils] = _Utils()
_UTC_TIME_DICT: Final[DatetimeDict] = U.datetime_to_dict(STARTUP.utc)
_LOCAL_TIME_DICT: Final[DatetimeDict] = U.datetime_to_dict(STARTUP.local)


class TyrannoJmesFunctions:
    """Collection of custom JMESPath functions."""

    def pep440_filter(self, versions: list[str], predicate: str) -> list[str]:
        return [U.sanitize_pep440(v) for v in versions if Pep440(v) in SpecifierSet(predicate)]

    def pep440_find_for_spec(self, spec: str) -> list[str]:
        pkg, predicate = U.split_pep440_spec(spec)
        versions = self.pypi_versions(pkg)
        return self.pep440_filter(versions, predicate)

    def pep440_ascending(self, versions: list[str]) -> list[str]:
        return [U.sanitize_pep440(p) for p in sorted(Pep440(v) for v in versions)]

    def pep440_descending(self, versions: list[str]) -> list[str]:
        return [U.sanitize_pep440(p) for p in sorted((Pep440(v) for v in versions), reverse=True)]

    def pep440_max_per(self, versions: list[str], per: str) -> str:
        # vrs = [Pep440(v) for v in versions]
        # TODO
        valid = {"major", "minor", "micro"}
        if per not in valid:
            msg = f"Argument '{per}' is not one of {valid}."
            raise JmesFunctionError.from_call(msg, depth=1)
        return U.sanitize_pep440(max(Pep440(v) for v in versions))

    def pep440_max(self, versions: list[str]) -> str:
        return U.sanitize_pep440(max(Pep440(v) for v in versions))

    def pep440_min(self, versions: list[str]) -> str:
        return U.sanitize_pep440(min(Pep440(v) for v in versions))

    def pep440(self, pep440_string: str) -> Pep440Dict:
        return U.pep440_info(Pep440(pep440_string))

    def pypi_versions(self, pkg: str) -> set[str]:
        return U.extract_pypi_versions(U.dl_pypi_metadata(pkg))

    def spdx_license(self, spdx_id: str) -> LicenseDict:
        return U.license_data(spdx_id)

    def timestamp(self, ts: str) -> DatetimeDict:
        return U.datetime_to_dict(datetime.fromisoformat(ts))

    def now_utc(self) -> DatetimeDict:
        return _UTC_TIME_DICT

    def now_local(self) -> DatetimeDict:
        return _LOCAL_TIME_DICT

    def pypi_data(self, package_name: str) -> dict[str, Any]:
        return U.dl_pypi_metadata(package_name)
