# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Environment variables and internal utils."""

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol, Self

import platformdirs

from tyranno_sandbox._about import __about__

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "STARTUP",
    "EnvGlobalVarsFactory",
    "GlobalConfigError",
    "GlobalVars",
    "GlobalVarsFactory",
    "Startup",
]


@dataclass(frozen=True)
class Startup:
    """When the app started (local and UTC), and a monotonic clock time."""

    local: datetime
    monotonic: float

    @classmethod
    def now(cls) -> Self:
        return cls(local=datetime.now().astimezone(), monotonic=time.monotonic())

    @cached_property
    def utc(self) -> datetime:
        return self.local.astimezone(UTC)

    def elapsed_seconds(self) -> float:
        return time.monotonic() - self.monotonic


class GlobalVarsFactory:
    """Factory that creates a [GlobalVars][] instance."""

    def __call__(self) -> GlobalVars:
        raise NotImplementedError


@dataclass(frozen=True, slots=True, kw_only=True)
class GlobalVars:
    """Collection of config values from environment variables and/or the platform."""

    cache_dir: Path
    config_dir: Path
    data_dir: Path
    log_dir: Path
    tyranno_dir: str
    log_format: str
    debug_mode: bool


@dataclass(frozen=True, slots=True)
class GlobalConfigError(Exception):
    """An error caused by an environment variable set incorrectly."""

    title: str
    value: str
    issue: str

    def __str__(self) -> str:
        return f"{self.title.title()} (={self.value}) {self.issue}."


class XdgDirFunction(Protocol):
    def __call__(
        self, *, appname: str, appauthor: str, version: str, ensure_exists: bool
    ) -> str: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class XdgHelper:
    """Helper that gets directories from XDG config or tyranno environment variables."""

    env: Mapping[str, str]

    def dir(self, xdg_fn: XdgDirFunction) -> Path:
        fn_name: str = xdg_fn.__name__  # ty:ignore[unresolved-attribute] # require a name
        var_name = self._var_name(fn_name)
        value: str
        title: str
        if v := self.env.get(var_name):
            value = v
            title = "$" + var_name
        else:
            value = xdg_fn(
                appname=__about__["name"],
                appauthor=__about__["vendor"],
                version=str(__about__["version_parts"].major),
                ensure_exists=False,
            )
            title = "platform config " + fn_name
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise GlobalConfigError(title, value, "is not an absolute path")
        if path.exists() and not path.is_dir():
            raise GlobalConfigError(title, value, "exists and is not a directory")
        return path

    @classmethod
    def _var_name(cls, fn_name: str) -> str:
        return "TYRANNO_" + fn_name.removeprefix("user_")


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvGlobalVarsFactory(GlobalVarsFactory):
    """Factory that reads from environment variables and platform config."""

    env: Mapping[str, str]

    def __call__(self) -> GlobalVars:
        xdg = XdgHelper(env=self.env)
        return GlobalVars(
            cache_dir=xdg.dir(platformdirs.user_cache_dir),
            config_dir=xdg.dir(platformdirs.user_config_dir),
            data_dir=xdg.dir(platformdirs.user_data_dir),
            log_dir=xdg.dir(platformdirs.user_log_dir),
            tyranno_dir=str(self._rel_dir("TYRANNO_DIR", Path(".tyranno"))),
            log_format=self._str("TYRANNO_LOG_FORMAT", ""),
            debug_mode=self._flag("TYRANNO_DEBUG_MODE"),
        )

    def _str(self, var: str, default: str) -> str:
        return self.env.get(var, default)

    def _flag(self, var: str, default: bool = False) -> bool:  # noqa: FBT001, FBT002
        if value := self.env.get(var):  # Treat empty the same as missing.
            return self.__parse_bool(var, value)
        return default

    def __parse_bool(self, var: str, value: str) -> bool:
        match value:
            case s if s == "1":
                return True
            case s if s == "0":
                return False
        raise GlobalConfigError("$" + var, value, "is neither 0 nor 1")

    def _rel_dir(self, var: str, default: Path) -> Path:
        if value := self.env.get(var):  # Treat empty the same as missing.
            path = Path(value)
            if path.is_absolute() or len(path.parts) > 1:
                raise GlobalConfigError("$" + var, value, "is not a relative path")
            return path
        return default


STARTUP: Final = Startup.now()
