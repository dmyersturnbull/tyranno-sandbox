# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Environment variables and internal utils.
"""

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cached_property
from pathlib import Path
from typing import ClassVar, Final, Self

import platformdirs

from tyranno_sandbox._about import __about__

__all__ = ["STARTUP", "EnvGlobalVarsFactory", "GlobalVars", "GlobalVarsFactory", "Startup"]

TRUE: Final[frozenset[str]] = frozenset({"true", "yes", "on"})
FALSE: Final[frozenset[str]] = frozenset({"false", "no", "off"})


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


STARTUP: Final[Startup] = Startup.now()


@dataclass(frozen=True, slots=True, kw_only=True)
class GlobalVars:
    """Collection of config values from environment variables and/or the platform."""

    cache_dir: Path
    config_dir: Path
    data_dir: Path
    tyranno_dir: str
    colorize: bool
    success_color: str
    failure_color: str


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
        var_name = self._var_name(xdg_fn.__name__)
        value = os.environ.get(var_name, xdg_fn(**self._args()))
        title = f"${var_name}" if var_name in os.environ else f"platform config {xdg_fn.__name__}"
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise GlobalConfigError(title, value, "is not an absolute path")
        if path.exists() and not path.is_dir():
            raise GlobalConfigError(title, value, "exists and is not a directory")
        return path

    def _var_name(self, fn_name: str) -> str:
        return "TYRANNO_" + fn_name.__name__.removeprefix("user_", "").upper()

    def _args[**P](self) -> P.kwargs:
        return {
            "appname": __about__["name"],
            "appauthor": __about__["vendor"],
            "version": __about__["version"],
            "roaming": False,
            "ensure_exists": False,
        }


GlobalVarsFactory = Callable[[], GlobalVars]


@dataclass(frozen=True, slots=True)
class EnvGlobalVarsFactory(GlobalVarsFactory):
    """Factory that reads from environment variables and platform config."""

    env_var_prefix: ClassVar[str] = "TYRANNO_"

    def __call__(self) -> GlobalVars:
        xdg = XdgHelper()
        return GlobalVars(
            cache_dir=xdg.dir(platformdirs.user_cache_dir),
            config_dir=xdg.dir(platformdirs.user_config_dir),
            data_dir=xdg.dir(platformdirs.user_data_dir),
            tyranno_dir=str(self._get_rel_dir("dir", ".tyranno")),
            success_color=self._get_str("success_color", "green"),
            failure_color=self._get_str("failure_color", "red"),
            colorize=self._get_bool("colorize"),
        )

    def _get_str(self, env_var: str, default: str) -> str:
        return os.environ.get(self.env_var_prefix + env_var, default)

    def _get_bool(self, name: str) -> bool:
        env_var = self.env_var_prefix + name.upper()
        value = os.environ.get(env_var, "false")
        return self._parse_bool(name, value)

    def _parse_bool(self, env_var: str, value: str) -> bool:
        match value.lower():
            case s if s in TRUE:
                return True
            case s if s in FALSE:
                return False
        raise GlobalConfigError("$" + env_var, value, f"is not ({'|'.join(TRUE | FALSE)})")

    def _get_rel_dir(self, name: str, default: str) -> str:
        var_name = self.env_var_prefix + name.upper()
        if value := os.environ.get(var_name):
            if Path(value).is_absolute() or len(Path(value).parts) > 1:
                raise GlobalConfigError("$" + var_name, value, "is not a relative path")
            return value
        return default
