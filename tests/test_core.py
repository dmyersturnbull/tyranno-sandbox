# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Tests for the `core` module."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tyranno_sandbox._core import JSON, Json

# Define a strategy for JSON primitives.
json_primitives = st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
)
# Define a strategy for lists and dicts.
json_data: st.SearchStrategy[Json] = st.recursive(
    json_primitives,
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=50,
)


class TestJson:
    """Tests for the recursive JSON types."""

    @given(data=json_data)
    def test_decode_encoded(self, data: Json) -> None:
        """Verify that `decode(encode(x)) == x` for all `x`."""
        assert JSON.decode(JSON.encode(data)) == data

    @given(data=json_data)
    def test_encode_decoded(self, data: Json) -> None:
        """Verify that `encode(decode(x)) == x` for all pretty-printed `x`."""
        encoded = JSON.encode(data)
        re_encoded = JSON.encode(JSON.decode(encoded))
        assert re_encoded == encoded


if __name__ == "__main__":
    pytest.main()
