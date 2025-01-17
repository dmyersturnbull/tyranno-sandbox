# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Environment variables and internal utils.
"""

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

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
    def __call__(self: Self) -> GlobalVars:
        raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class DefaultGlobalVarsFactory(GlobalVarsFactory):
    def __call__(self: Self) -> GlobalVars:
        _now_utc = datetime.now(UTC)
        _user_cache_path = platformdirs.user_cache_path("cicd")
        return GlobalVars(
            now_utc=_now_utc,
            now_local=_now_utc.astimezone(),
            cache_dir=Path(os.environ.get("CICD_CACHE_DIR", platformdirs.user_cache_path("cicd"))),
            config_dir=Path(os.environ.get("CICD_CONFIG_DIR", platformdirs.user_config_path("cicd"))),
            trash_dir_name=".#trash~",
        )
