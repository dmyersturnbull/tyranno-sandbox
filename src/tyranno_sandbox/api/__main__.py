# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Entrypoint for server.
"""

import asyncio
import os

if os.name == "nt":
    # workaround for asyncio loop policy for Windows users
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from tyranno_sandbox.api.server import api  # noqa: F401
