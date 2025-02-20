# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Environment variables and internal utils.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import platformdirs

__all__ = ["DefaultGlobalVarsFactory", "GlobalVars", "GlobalVarsFactory"]


@dataclass(frozen=True, slots=True, kw_only=True)
class GlobalVars:
    now_utc: datetime
    now_local: datetime
    cache_dir: Path
    config_dir: Path
    trash_dir_name: str


@dataclass(frozen=True, slots=True)
class GlobalVarsFactory:
    def __call__(self) -> GlobalVars:
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class DefaultGlobalVarsFactory(GlobalVarsFactory):
    def __call__(self) -> GlobalVars:
        now_utc = datetime.now(ZoneInfo("Etc/UTC"))
        return GlobalVars(
            now_utc=now_utc,
            now_local=now_utc.astimezone(),
            cache_dir=Path(os.environ.get("TYRANNO_CACHE_DIR", platformdirs.user_cache_path("tyranno"))),
            config_dir=Path(os.environ.get("TYRANNO_CONFIG_DIR", platformdirs.user_config_path("tyranno"))),
            trash_dir_name=".#trash~",
        )
