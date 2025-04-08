# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""
Tyrannosaurus metadata and entry point.
"""

from tyranno_sandbox._about import __about__

__uri__ = __about__["urls"]["homepage"]
__title__ = __about__["name"]
__summary__ = __about__["summary"]
__version__ = __about__["version"]
__license__ = __about__["license"]
