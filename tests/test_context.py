# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Unit and integration tests for context.py expression evaluation."""

from typing import TYPE_CHECKING

import pytest

from tyranno_sandbox.context import Context, Data, ExpressionError
from tyranno_sandbox.dot_tree import DotTree
from tyranno_sandbox.global_vars import GlobalVars
from tyranno_sandbox.sync import SyncHelper

if TYPE_CHECKING:
    from pathlib import Path


def _make_data(raw: dict) -> Data:
    return Data(DotTree.from_nested(raw))


@pytest.fixture
def data() -> Data:
    return _make_data(
        {
            "project": {
                "name": "my-project",
                "description": "A test project",
                "version": "1.2.3",
                "keywords": ["alpha", "beta", "gamma"],
                "urls": {"Homepage": "https://example.com/my-project"},
            },
            "tool": {"tyranno": {"data": {"vendor": "acme", "namespace": "my_project"}}},
        }
    )


@pytest.fixture
def env(tmp_path: Path) -> GlobalVars:
    return GlobalVars(
        cache_dir=tmp_path / "cache",
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        log_dir=tmp_path / "log",
        tyranno_dir=".tyranno",
        log_format="",
        debug_mode=False,
    )


class TestReplaceVarsIn:
    def test_no_expressions(self, data: Data) -> None:
        assert data.replace_vars_in("no vars here") == "no vars here"

    def test_single_expression(self, data: Data) -> None:
        assert data.replace_vars_in("$<<project.name>>") == "my-project"

    def test_multiple_expressions(self, data: Data) -> None:
        result = data.replace_vars_in("$<<project.name>> v$<<project.version>>")
        assert result == "my-project v1.2.3"

    def test_expression_surrounded_by_text(self, data: Data) -> None:
        result = data.replace_vars_in("name = $<<project.name>> end")
        assert result == "name = my-project end"

    def test_list_value_comma_separated(self, data: Data) -> None:
        result = data.replace_vars_in("$<<project.keywords>>")
        assert result == "alpha, beta, gamma"


class TestExpandVarSimpleKeys:
    def test_dotted_key(self, data: Data) -> None:
        assert data.expand_var("project.name") == "my-project"

    def test_nested_key(self, data: Data) -> None:
        assert data.expand_var("project.urls.Homepage") == "https://example.com/my-project"

    def test_dollar_prefix(self, data: Data) -> None:
        assert data.expand_var("$.project.name") == "my-project"

    def test_at_prefix(self, data: Data) -> None:
        assert data.expand_var("@.vendor") == "acme"

    def test_dot_prefix_resolves_to_tyranno_data(self, data: Data) -> None:
        assert data.expand_var(".vendor") == "acme"

    def test_empty_expression(self, data: Data) -> None:
        assert data.expand_var("") == ""


class TestExpandVarPipeSyntax:
    def test_pipe_to_lower(self, data: Data) -> None:
        assert data.expand_var("project.name | lower(@)") == "my-project"

    def test_pipe_to_upper(self, data: Data) -> None:
        assert data.expand_var("project.name | upper(@)") == "MY-PROJECT"

    def test_pipe_to_yaml(self, data: Data) -> None:
        result = data.expand_var("project.urls.Homepage | yaml(@)")
        assert "example.com" in result

    def test_pipe_list_to_yaml(self, data: Data) -> None:
        result = data.expand_var("project.keywords | yaml(@)")
        assert "- alpha" in result

    def test_chained_pipes(self, data: Data) -> None:
        result = data.expand_var("project.name | upper(@) | lower(@)")
        assert result == "my-project"

    def test_pipe_replace(self, data: Data) -> None:
        result = data.expand_var("project.name | replace(@, '-', '_')")
        assert result == "my_project"


class TestExpandVarPep440:
    def test_pep440_minor(self, data: Data) -> None:
        assert data.expand_var("project.version | pep440_minor(@)") == "1.2"


class TestExpandVarNowUtc:
    def test_now_utc_year(self, data: Data) -> None:
        result = data.expand_var("now_utc().year")
        assert result.isdigit()
        assert 2020 <= int(result) <= 2100

    def test_now_utc_month(self, data: Data) -> None:
        result = data.expand_var("now_utc().month")
        assert result.isdigit()
        assert 1 <= int(result) <= 12

    def test_now_local_year(self, data: Data) -> None:
        result = data.expand_var("now_local().year")
        assert result.isdigit()


class TestExpandVarErrors:
    def test_missing_key_raises(self, data: Data) -> None:
        with pytest.raises(ExpressionError, match="not found"):
            data.expand_var("project.nonexistent")

    def test_unknown_function_raises(self, data: Data) -> None:
        with pytest.raises(ExpressionError, match="Unknown function"):
            data.expand_var("project.name | no_such_func(@)")

    def test_bad_attribute_raises(self, data: Data) -> None:
        with pytest.raises(ExpressionError):
            data.expand_var("now_utc().no_such_attr")


class TestIntegration:
    def test_replace_vars_in_full_template(self, data: Data) -> None:
        template = 'name = "$<<project.name>>" version = "$<<project.version>>"'
        result = data.replace_vars_in(template)
        assert result == 'name = "my-project" version = "1.2.3"'

    def test_dot_prefix_in_tyranno_data(self, data: Data) -> None:
        result = data.replace_vars_in("$<<.vendor>>")
        assert result == "acme"

    def test_at_prefix_in_tyranno_data(self, data: Data) -> None:
        result = data.replace_vars_in("$<<@.vendor>>")
        assert result == "acme"


class TestSyncHelperIntegration:
    def test_inline_replacement(self, tmp_path: Path, data: Data, env: GlobalVars) -> None:
        ctx = Context(env=env, repo_dir=tmp_path, data=data, dry_run=True)

        target = tmp_path / "test.toml"
        target.write_text(
            '# ::tyranno:: name = "$<<project.name>>"\nname = "old-value"\n', encoding="utf-8"
        )

        helper = SyncHelper(ctx, target)
        helper.run()

        assert helper.new_lines[0].startswith("# ::tyranno::")
        assert helper.new_lines[1] == 'name = "my-project"'

    def test_multiple_consecutive_tyranno_lines(
        self, tmp_path: Path, data: Data, env: GlobalVars
    ) -> None:
        ctx = Context(env=env, repo_dir=tmp_path, data=data, dry_run=True)

        target = tmp_path / "test.toml"
        target.write_text(
            "# ::tyranno:: $<<project.name>>\n"
            "# ::tyranno:: $<<project.version>>\n"
            "old-name\n"
            "old-version\n",
            encoding="utf-8",
        )

        helper = SyncHelper(ctx, target)
        helper.run()

        assert helper.new_lines[2] == "my-project"
        assert helper.new_lines[3] == "1.2.3"

    def test_non_tyranno_lines_unchanged(self, tmp_path: Path, data: Data, env: GlobalVars) -> None:
        ctx = Context(env=env, repo_dir=tmp_path, data=data, dry_run=True)

        target = tmp_path / "test.toml"
        content = "# regular comment\nsome_key = 'value'\n"
        target.write_text(content, encoding="utf-8")

        helper = SyncHelper(ctx, target)
        helper.run()

        assert helper.new_lines == ["# regular comment", "some_key = 'value'"]
        assert helper.hits == []
