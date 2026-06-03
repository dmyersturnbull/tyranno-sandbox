# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the Tyranno function registry."""

from tyranno_sandbox.tyranno_functions import (
    from_json,
    from_yaml,
    join,
    now_local,
    now_utc,
    pep440,
    pep440_minor,
    semver,
    sort,
    timestamp,
    yaml,
    yaml_multiline,
)


class TestYamlFunc:
    def test_plain_string(self) -> None:
        assert yaml("hello world") == "hello world"

    def test_string_needing_quotes(self) -> None:
        result = yaml("with: colon")
        assert result == "'with: colon'"

    def test_boolean_string_gets_quoted(self) -> None:
        result = yaml("true")
        assert result == "'true'"

    def test_url_is_valid_yaml_scalar(self) -> None:
        result = yaml("https://example.com")
        assert "example.com" in result

    def test_list_becomes_block_sequence(self) -> None:
        result = yaml(["alpha", "beta"])
        assert "- alpha" in result
        assert "- beta" in result

    def test_integer(self) -> None:
        result = yaml(42)
        assert result == "42"


class TestFromYaml:
    def test_parses_scalar(self) -> None:
        assert from_yaml("hello") == "hello"

    def test_parses_sequence(self) -> None:
        result = from_yaml("- a\n- b")
        assert result == ["a", "b"]

    def test_roundtrip(self) -> None:
        original = ["ci/cd", "python"]
        dumped = yaml(original)
        parsed = from_yaml(dumped)
        assert parsed == original


class TestFromJson:
    def test_parses_object(self) -> None:
        result = from_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parses_array(self) -> None:
        result = from_json('["a", "b"]')
        assert result == ["a", "b"]


class TestPep440:
    def test_minor_version(self) -> None:
        result = pep440("1.2.3")
        assert result["minor_version"] == "1.2"

    def test_major_minor_micro(self) -> None:
        result = pep440("3.14.1")
        assert result["major"] == 3
        assert result["minor"] == 14
        assert result["micro"] == 1

    def test_pre_release(self) -> None:
        result = pep440("1.0.0a1")
        assert result["pre_type"] == "a"
        assert result["pre_number"] == 1

    def test_no_pre_release(self) -> None:
        result = pep440("2.0.0")
        assert result["pre"] == ""
        assert result["pre_type"] == ""


class TestPep440Minor:
    def test_strips_patch(self) -> None:
        assert pep440_minor("1.2.3") == "1.2"

    def test_large_minor(self) -> None:
        assert pep440_minor("3.14.0") == "3.14"


class TestSemver:
    def test_major_minor_patch(self) -> None:
        result = semver("1.2.3")
        assert result["major"] == 1
        assert result["minor"] == 2
        assert result["patch"] == 3

    def test_minor_version_string(self) -> None:
        result = semver("2.5.0")
        assert result["minor_version"] == "2.5"

    def test_pre_release(self) -> None:
        result = semver("1.0.0-alpha.1")
        assert result["pre"] == "alpha.1"

    def test_no_pre_release(self) -> None:
        result = semver("1.2.3")
        assert result["pre"] == ""


class TestTimestamp:
    def test_parses_iso_datetime(self) -> None:
        result = timestamp("2025-06-15T10:30:00+00:00")
        assert result["year"] == 2025
        assert result["month"] == 6
        assert result["day"] == 15

    def test_unix_time(self) -> None:
        result = timestamp("2025-01-01T00:00:00+00:00")
        assert result["unix_time"] == 1735689600


class TestSourceFuncs:
    def test_now_utc_returns_time_dict(self) -> None:
        result = now_utc()
        assert isinstance(result, dict)
        assert "year" in result
        assert "unix_time" in result

    def test_now_local_returns_time_dict(self) -> None:
        result = now_local()
        assert isinstance(result, dict)
        assert "year" in result

    def test_now_utc_is_startup_time(self) -> None:
        from tyranno_sandbox.global_vars import STARTUP

        result = now_utc()
        assert result["unix_time"] == int(STARTUP.utc.timestamp())

    def test_now_utc_year_is_reasonable(self) -> None:
        result = now_utc()
        assert 2020 <= result["year"] <= 2100

    def test_now_utc_and_now_local_same_instant(self) -> None:
        utc = now_utc()
        local = now_local()
        assert utc["unix_time"] == local["unix_time"]


class TestYamlMultiline:
    def test_basic(self) -> None:
        assert yaml_multiline("alpha, beta, gamma") == "alpha\nbeta\ngamma"

    def test_with_indent(self) -> None:
        assert yaml_multiline("a, b", 2) == "  a\n  b"

    def test_list_input(self) -> None:
        assert yaml_multiline(["x", "y"]) == "x\ny"


class TestSort:
    def test_csv_string(self) -> None:
        assert sort("banana, apple, cherry") == "apple, banana, cherry"

    def test_list_input(self) -> None:
        assert sort(["gamma", "alpha", "beta"]) == "alpha, beta, gamma"


class TestJoin:
    def test_default_sep(self) -> None:
        assert join("a, b, c") == "a, b, c"

    def test_custom_sep(self) -> None:
        assert join("a, b, c", " | ") == "a | b | c"

    def test_list_input(self) -> None:
        assert join(["x", "y", "z"], "-") == "x-y-z"
