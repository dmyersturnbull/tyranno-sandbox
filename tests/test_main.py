# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Tests."""

import pytest

# noinspection PyUnresolvedReferences
from tyranno_sandbox._about import __about__ as about


class TestAbout:
    """Tests for running the app."""

    def test_about(self) -> None:
        assert about["namespace"] == "tyranno_sandbox"


if __name__ == "__main__":
    pytest.main()
