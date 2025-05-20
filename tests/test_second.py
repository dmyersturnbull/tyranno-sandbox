# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""
Tests.
"""

import pytest

from tyranno_sandbox._about import __about__ as about


@pytest.fixture
def fixture() -> str:
    return "fixture"


class TestSecond:
    """Tests for running the app."""

    def test_name(self) -> None:
        assert about["name"] == "tyranno-sandbox"


if __name__ == "__main__":
    pytest.main()
