# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Tests."""

import pytest
from tests import Helper

from tyranno_sandbox._about import __about__ as about


@pytest.fixture
def helper() -> Helper:
    return Helper.new()


class TestSecond:
    """Tests for running the app."""

    def test_name(self) -> None:
        assert about["name"] == "tyranno-sandbox"

    def test_misc(self, helper) -> None:  # noqa: ANN001
        assert helper.start.mono_ns > 0


if __name__ == "__main__":
    pytest.main()
