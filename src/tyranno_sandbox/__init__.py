# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Tyrannosaurus.

Users should import from this module.

Example:
    ```python
    from tyranno_sandbox import __about__, Context
    ```
"""

from tyranno_sandbox._about import __about__
from tyranno_sandbox._core import Json, JsonArray, JsonBranch, JsonPrimitive
from tyranno_sandbox._global_vars import STARTUP, GlobalConfigError, GlobalVars, GlobalVarsFactory
from tyranno_sandbox.context import Context, ContextFactory, DefaultContextFactory
from tyranno_sandbox.dot_tree import DotTree, DotTrees, LeavesInCommonError
from tyranno_sandbox.james import JmesFunctionError, TyrannoJmesFunctions
from tyranno_sandbox.sync import Syncer

__all__ = [
    "STARTUP",
    "Context",
    "ContextFactory",
    "DefaultContextFactory",
    "DotTree",
    "DotTrees",
    "GlobalConfigError",
    "GlobalVars",
    "GlobalVarsFactory",
    "JmesFunctionError",
    "Json",
    "JsonArray",
    "JsonBranch",
    "JsonPrimitive",
    "LeavesInCommonError",
    "Syncer",
    "TyrannoJmesFunctions",
]

__uri__ = __about__["urls"]["homepage"]
__title__ = __about__["name"]
__summary__ = __about__["summary"]
__version__ = __about__["version"]
__license__ = __about__["license"]
