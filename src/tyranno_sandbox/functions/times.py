# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

import calendar
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar, NamedTuple, TypedDict

from tyranno_sandbox.functions._core import FunctionError


class DateTuple(NamedTuple):
    year: int
    month: int
    day: int


class TimeTuple(NamedTuple):
    hour: int
    minute: int
    second: int
    microsecond: int


class TimeDict(TypedDict):
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


@dataclass(frozen=True, slots=True)
class DatetimeFunctions:
    # IANA timezones that are aliases for Etc/UTC.
    UTC_NAMES: ClassVar = frozenset({"Etc/UTC", "Etc/Universal", "Etc/UCT", "Etc/Zulu"})

    def parse(self, s: str) -> datetime:
        return datetime.fromisoformat(s)

    def format(self, dt: datetime, *, sep: str = "T", ts: str = "microseconds") -> str:
        if not (tz := dt.tzname()):
            msg = f"Datetime instance {dt} is not zoned."
            raise FunctionError.from_call(msg, depth=2)
        stamp = dt.isoformat(sep, ts)
        # Don't replace +00:00 with Z for Europe/London (canonical), Europe/Jersey, etc.
        if tz.removeprefix("Etc/") in self.UTC_NAMES:
            # I couldn't confirm that Python never uses -00:00, which RFC 3339 supports.
            # ISO 8601 inexplicably supports ±, but let's not check that.
            stamp = stamp.replace("+00:00", "Z").replace("-00:00", "Z")
        return stamp

    def of(self, dt: datetime) -> TimeDict:
        # starting at 1
        week_of_month: int = math.ceil(dt.day + dt.replace(day=1).weekday() / 7)
        rfc_9557 = self.format(dt) + (f"[{dt.tzname()}]" if dt.tzname() else "")
        return TimeDict(
            rfc_9557=rfc_9557,
            rfc_9557_utc=self.format(dt.astimezone(UTC)) + "[Etc/UTC]",
            rfc_3339=self.format(dt),
            rfc_3339_utc=self.format(dt.astimezone(UTC)),
            iso_8601_week_date=dt.strftime("%G-W%V-%u"),
            unix_time=int(dt.timestamp()),
            formatted_local=dt.strftime("%Y-%m-%d %H:%M:%S"),
            formatted=self.format(dt, sep=" ", ts="seconds"),
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
