# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Environment variables and internal utils."""

import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cached_property
from pathlib import Path
from typing import Final, Self

import platformdirs

from tyranno_sandbox._about import __about__

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


STARTUP: Final = Startup.now()


@dataclass(frozen=True, slots=True, kw_only=True)
class GlobalVars:
    """Collection of config values from environment variables and/or the platform."""

    cache_dir: Path
    config_dir: Path
    data_dir: Path
    log_dir: Path
    tyranno_dir: str
    use_color: bool
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


@dataclass(frozen=True, slots=True, kw_only=True)
class XdgHelper[**P]:
    """Helper that gets directories from XDG config or tyranno environment variables."""

    env: Mapping[str, str | None]

    def dir(self, xdg_fn: Callable[P, str]) -> Path:
        fn_name: str = xdg_fn.__name__  # ty: ignore[unresolved-attribute]
        var_name = self._var_name(fn_name)
        value = self.env.get(var_name, xdg_fn(**self._args()))
        title = "$" + var_name if var_name in self.env else f"platform config {fn_name}"
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise GlobalConfigError(title, value, "is not an absolute path")
        if path.exists() and not path.is_dir():
            raise GlobalConfigError(title, value, "exists and is not a directory")
        return path

    @staticmethod
    def _var_name(fn_name: str) -> str:
        return "TYRANNO_" + fn_name.removeprefix("user_")

    @staticmethod
    def _args[**P]() -> P.kwargs:
        return {
            "appname": __about__["name"],
            "appauthor": __about__["vendor"],
            "version": str(__about__["version_parts"].major),
            "roaming": False,
            "ensure_exists": False,
        }


OUT_IS_TTY: Final = sys.stdout.isatty()
ERR_IS_TTY: Final = sys.stdout.isatty()
GlobalVarsFactory = Callable[[], GlobalVars]


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvGlobalVarsFactory(GlobalVarsFactory):
    """Factory that reads from environment variables and platform config."""

    env: Mapping[str, str | None]

    def __call__(self) -> GlobalVars:
        xdg = XdgHelper(env=self.env)
        return GlobalVars(
            cache_dir=xdg.dir(platformdirs.user_cache_dir),
            config_dir=xdg.dir(platformdirs.user_config_dir),
            data_dir=xdg.dir(platformdirs.user_data_dir),
            log_dir=xdg.dir(platformdirs.user_log_dir),
            use_color=self._use_color(),
            tyranno_dir=str(self._rel_dir("TYRANNO_DIR", Path(".tyranno"))),
            log_format=self._str("TYRANNO_LOG_FORMAT", ""),
            debug_mode=self._flag("TYRANNO_DEBUG_MODE"),
        )

    def _use_color(self) -> bool:
        # See https://force-color.org/) and https://no-color.org/
        return self._flag("FORCE_COLOR", self._flag("NO_COLOR", OUT_IS_TTY))

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
