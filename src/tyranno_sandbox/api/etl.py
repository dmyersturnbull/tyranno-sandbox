# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Example ETL to run in the background."""

import os
from typing import Final

MONGO_URI: Final[str | None] = os.environ.get("MONGO_URI")
