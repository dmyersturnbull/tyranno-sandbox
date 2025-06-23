# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Environment variables and internal utils."""

import os
import sys
import time
from collections.abc import Callable
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


class XdgHelper[**P]:
    """Helper that gets directories from XDG config or tyranno environment variables."""

    def dir(self, xdg_fn: Callable[P, str]) -> Path:
        fn_name: str = xdg_fn.__name__  # ty: ignore[unresolved-attribute]
        var_name = self._var_name(fn_name)
        value = os.environ.get(var_name, xdg_fn(**self._args()))
        title = "$" + var_name if var_name in os.environ else f"platform config {fn_name}"
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise GlobalConfigError(title, value, "is not an absolute path")
        if path.exists() and not path.is_dir():
            raise GlobalConfigError(title, value, "exists and is not a directory")
        return path

    def _var_name(self, fn_name: str) -> str:
        return "TYRANNO_" + fn_name.removeprefix("user_")

    def _args[**P](self) -> P.kwargs:
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


@dataclass(frozen=True, slots=True)
class EnvGlobalVarsFactory(GlobalVarsFactory):
    """Factory that reads from environment variables and platform config."""

    def __call__(self) -> GlobalVars:
        xdg = XdgHelper()
        return GlobalVars(
            cache_dir=xdg.dir(platformdirs.user_cache_dir),
            config_dir=xdg.dir(platformdirs.user_config_dir),
            data_dir=xdg.dir(platformdirs.user_data_dir),
            log_dir=xdg.dir(platformdirs.user_log_dir),
            tyranno_dir=str(self._rel_dir("TYRANNO_DIR", ".tyranno")),
            use_color=self._use_color(),
            log_format=self._str("TYRANNO_LOG_FORMAT", ""),
            debug_mode=self._bool("TYRANNO_DEBUG_MODE"),
        )

    def _use_color(self) -> bool:
        if self._bool("FORCE_COLOR") == "1":
            return True
        if self._bool("NO_COLOR") == "1":
            return False
        return self._bool("colorize", lambda: OUT_IS_TTY)

    def _str(self, var: str, default: str) -> str:
        return os.environ.get(var, default)

    def _bool(self, var: str, default: Callable[[], bool] = lambda: False) -> bool:
        value = default() if os.environ.get(var, "auto") == "auto" else os.environ[var]
        return self.__parse_bool(var, value)

    def __parse_bool(self, var: str, value: str) -> bool:
        match value:
            case s if s == "1":
                return True
            case s if s == "0":
                return False
        raise GlobalConfigError("$" + var, value, "is not 0 or 1")

    def _rel_dir(self, var: str, default: str) -> str:
        if value := os.environ.get(var):
            if Path(value).is_absolute() or len(Path(value).parts) > 1:
                raise GlobalConfigError("$" + var, value, "is not a relative path")
            return value
        return default
