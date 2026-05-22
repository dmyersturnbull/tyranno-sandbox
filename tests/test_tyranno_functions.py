# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the Tyranno function registry."""

import pytest

from tyranno_sandbox.tyranno_functions import FUNCS, SOURCE_FUNCS


class TestYamlFunc:
    def test_plain_string(self) -> None:
        assert FUNCS["yaml"]("hello world") == "hello world"

    def test_string_needing_quotes(self) -> None:
        result = FUNCS["yaml"]("with: colon")
        assert result == "'with: colon'"

    def test_boolean_string_gets_quoted(self) -> None:
        result = FUNCS["yaml"]("true")
        assert result == "'true'"

    def test_url_is_valid_yaml_scalar(self) -> None:
        result = FUNCS["yaml"]("https://example.com")
        assert "example.com" in result

    def test_list_becomes_block_sequence(self) -> None:
        result = FUNCS["yaml"](["alpha", "beta"])
        assert "- alpha" in result
        assert "- beta" in result

    def test_integer(self) -> None:
        result = FUNCS["yaml"](42)
        assert result == "42"


class TestFromYaml:
    def test_parses_scalar(self) -> None:
        assert FUNCS["from_yaml"]("hello") == "hello"

    def test_parses_sequence(self) -> None:
        result = FUNCS["from_yaml"]("- a\n- b")
        assert result == ["a", "b"]

    def test_roundtrip(self) -> None:
        original = ["ci/cd", "python"]
        dumped = FUNCS["yaml"](original)
        parsed = FUNCS["from_yaml"](dumped)
        assert parsed == original


class TestFromJson:
    def test_parses_object(self) -> None:
        result = FUNCS["from_json"]('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parses_array(self) -> None:
        result = FUNCS["from_json"]('["a", "b"]')
        assert result == ["a", "b"]


class TestStringFuncs:
    def test_lower(self) -> None:
        assert FUNCS["lower"]("Hello World") == "hello world"

    def test_upper(self) -> None:
        assert FUNCS["upper"]("hello") == "HELLO"

    def test_replace(self) -> None:
        assert FUNCS["replace"]("foo_bar", "_", "-") == "foo-bar"

    def test_sort(self) -> None:
        assert FUNCS["sort"]("banana, apple, cherry") == "apple, banana, cherry"

    def test_join_default_sep(self) -> None:
        assert FUNCS["join"]("a, b, c") == "a, b, c"

    def test_join_custom_sep(self) -> None:
        assert FUNCS["join"]("a, b, c", " | ") == "a | b | c"

    def test_spdx_license(self) -> None:
        assert FUNCS["spdx_license"]("Apache-2.0") == "Apache-2.0"

    def test_pep440_minor(self) -> None:
        assert FUNCS["pep440_minor"]("1.2.3") == "1.2"

    def test_pep440_minor_strips_patch(self) -> None:
        assert FUNCS["pep440_minor"]("3.14.0") == "3.14"


class TestSourceFuncs:
    def test_now_utc_returns_datetime(self) -> None:
        import datetime

        result = SOURCE_FUNCS["now_utc"]()
        assert isinstance(result, datetime.datetime)
        assert result.tzinfo is not None

    def test_now_local_returns_datetime(self) -> None:
        import datetime

        result = SOURCE_FUNCS["now_local"]()
        assert isinstance(result, datetime.datetime)

    def test_now_utc_is_startup_time(self) -> None:
        from tyranno_sandbox._global_vars import STARTUP

        result = SOURCE_FUNCS["now_utc"]()
        assert result == STARTUP.utc

    def test_now_utc_year_is_reasonable(self) -> None:
        result = SOURCE_FUNCS["now_utc"]()
        assert 2020 <= result.year <= 2100

    def test_now_utc_and_now_local_differ_only_by_timezone(self) -> None:
        utc = SOURCE_FUNCS["now_utc"]()
        local = SOURCE_FUNCS["now_local"]()
        import datetime

        diff = abs((utc - local.astimezone(datetime.timezone.utc)).total_seconds())
        assert diff < 1  # same instant


class TestYamlMultiline:
    def test_basic(self) -> None:
        result = FUNCS["yaml_multiline"]("alpha, beta, gamma")
        lines = result.splitlines()
        assert len(lines) == 3

    def test_with_indent(self) -> None:
        result = FUNCS["yaml_multiline"]("a, b", "2")
        assert all(line.startswith("  ") for line in result.splitlines())
