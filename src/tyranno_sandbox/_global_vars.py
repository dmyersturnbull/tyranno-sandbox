# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Environment variables and internal utils.
"""

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryFile
from typing import Literal
from zoneinfo import ZoneInfo

import platformdirs

from tyranno_sandbox._about import __about__

__all__ = ["DefaultGlobalVarsFactory", "GlobalVars", "GlobalVarsFactory"]


@dataclass(frozen=True, slots=True, kw_only=True)
class GlobalVars:
    now_utc: datetime
    now_local: datetime
    cache_dir: Path
    config_dir: Path
    data_dir: Path
    trash_dir_name: str


@dataclass(frozen=True, slots=True)
class GlobalVarsFactory:
    def __call__(self) -> GlobalVars:
        raise NotImplementedError()


class GlobalConfigError(Exception):
    def __init__(self, key: str, source: str, value: str, issue: str) -> None:
        self.key = key
        self.value = value
        self.source = source
        self.issue = issue

    def __str__(self) -> str:
        return f"{self.key.title()} (={self.value} from {self.source}) is invalid: {self.issue}."


class DirHelper:
    def get_dir(self, key: str, source: str, value: str, is_abs: Literal["yes", "no", "*"]) -> Path:
        path = Path(value)
        if is_abs == "yes":
            path = path.expanduser()
        try:
            self._test_dir(path)
        except OSError as e:
            raise GlobalConfigError(key, source, value, e.strerror)
        if is_abs == "yes" and not path.is_absolute():
            raise GlobalConfigError(key, source, value, "Not an absolute path")
        if is_abs == "no" and path.is_absolute():
            raise GlobalConfigError(key, source, value, "Not a relative path")
        return path

    def _test_dir(self, path: Path) -> None:
        if path.exists():
            path.iterdir()
        else:
            with TemporaryFile(dir=path):
                pass


class XdgHelper[**P](DirHelper):
    def dir(self, name: str, xdg_fn: Callable[P, str]) -> Path:
        var_name = f"TYRANNO_{name.upper()}_DIR"
        source = "env var" if var_name in os.environ else "platform config"
        value = os.environ.get(var_name, xdg_fn(**self._args()))
        return self.get_dir(f"{name} / ${var_name}", source, value, "yes")

    def _args[**P](self) -> P.kwargs:
        return {
            "appname": __about__.name,
            "appauthor": __about__.author,
            "version": __about__.version,
            "roaming": False,
            "ensure_exists": False,
        }


class TrashDirHelper(DirHelper):
    def dir(self) -> Path:
        var_name = "TYRANNO_TRASH_DIR_NAME"
        value = os.environ.get("TYRANNO_TRASH_DIR_NAME", ".~trash#")
        source = "env var" if var_name in os.environ else "default"
        return self.get_dir("trash directory name / $TYRANNO_TRASH_DIR_NAME", source, value, "no")


@dataclass(frozen=True, slots=True)
class DefaultGlobalVarsFactory(GlobalVarsFactory):
    """"""

    def __call__(self) -> GlobalVars:
        now_utc = datetime.now(ZoneInfo("Etc/UTC"))
        h = XdgHelper()
        return GlobalVars(
            now_utc=now_utc,
            now_local=now_utc.astimezone(),
            cache_dir=h.dir("cache", platformdirs.user_cache_dir),
            config_dir=h.dir("config", platformdirs.user_config_dir),
            data_dir=h.dir("data", platformdirs.user_data_dir),
            trash_dir_name=str(TrashDirHelper().dir()),
        )
