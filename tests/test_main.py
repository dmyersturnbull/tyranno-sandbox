# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""
Tests.
"""

import pytest
from typing import Self


class TestApp:
    """Tests for running the app."""

    def test_it(self: Self) -> None:
        assert True


if __name__ == "__main__":
    pytest.main()
