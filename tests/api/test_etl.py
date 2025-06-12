# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Tests for ETL."""

import pytest

from .. import logger

pymongo = pytest.importorskip("pymongo")
logger.info("Running ETL tests.")
