# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Example ETL to run in background.
"""

import os
from typing import Final

MONGO_URI: Final[str] = os.environ["MONGO_URI"]
