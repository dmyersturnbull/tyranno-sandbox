# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

# https://github.com/casey/just
# https://just.systems/man/en/
# https://cheatography.com/linux-china/cheat-sheets/justfile/

set ignore-comments	:= true

###################################################################################################

# List available recipes.
[group('help')]
list:
  @just --list
alias help := list

###################################################################################################

# Sync the venv and install commit hooks.
[group('project')]
init:
  uv sync --all-extras --exact
  uv run pre-commit install --install-hooks --overwrite
  uv run pre-commit gc

# Update the lock file, sync the venv, auto-fix + format changes, and clean.
[group('project')]
revamp: update-lock update-hooks fix-changes format-changes clean

# Lock and sync the venv exactly with all extras.
[group('project')]
sync:
  uv sync --all-extras --exact
alias lock := sync

# Update pre-commit hooks, update the lock file, and sync the venv.
[group('project')]
update: update-lock update-hooks
alias upgrade := update

# Update the lock file and sync the venv.
[group('project')]
update-lock:
  uv sync --upgrade --all-extras --exact
  uv run pre-commit gc
alias upgrade-lock := update-lock

# Auto-update commit hooks.
[group('project')]
update-hooks:
  uv run pre-commit autoupdate
  uv run pre-commit gc
alias upgrade-hooks := update-hooks

# Remove temporary files.
[group('project')]
clean: && trash
  uv cache prune
  uv run pre-commit gc

# Delete temporary project files and directories.
[group('project'), private]
@trash:
  - rm -f .coverage.json
  - rm -rf .ruff_cache/
  - rm -rf .hypothesis/
  - rm -rf **/__pycache__/
  - rm -rf **/.pytest_cache/
  - rm -rf **/cython_debug/
  - rm -rf **/*.egg-info/
  - rm -f **/*.py[codi]

# Delete files whose names indicate they're temporary.
[group('project'), private]
@trash-unsafe:
  - rm -f **/.DS_Store
  - rm -f **/Thumbs.db
  - rm -f **/*.tmp
  - rm -f **/*.temp
  - rm -f **/*.swp
  - rm -f **/.#*
  - rm -f **/*[~\$]
  - rm -f **/*.directory

###################################################################################################

# Format modified files (via pre-commit).
[group('format')]
format-changes: _format
alias format := format-changes

# Format ALL files (via pre-commit).
[group('format')]
format-all: (_format "--all-files")

_format *args:
  uv run pre-commit run end-of-file-fixer {{args}}
  uv run pre-commit run fix-byte-order-marker {{args}}
  uv run pre-commit run trailing-whitespace {{args}}
  uv run pre-commit run ruff-format {{args}}
  uv run pre-commit run prettier {{args}}

###################################################################################################

# Fix Ruff rule violations in modified files (via pre-commit).
[group('fix')]
fix-changes: _fix
alias fix := fix-changes

# Fix Ruff rule violations in ALL files (via pre-commit).
[group('fix')]
fix-all: (_fix "--all-files")

# Fix Ruff rule violations.
[group('fix')]
fix-ruff *args: (_fix_ruff args)

# Fix Ruff rule violations, including preview, unsafe, and noqa-suppressed.
[group('fix')]
fix-ruff-unsafe *args: (_fix_ruff "--preview" "--unsafe-fixes" "--ignore-noqa" args)

_fix *args:
  - uv run pre-commit run ruff-fix {{args}}

_fix_ruff *args:
  - uv run ruff check --fix-only --show-fixes --statistics --output-format grouped {{args}}

###################################################################################################

# Check Ruff and Pyright rules (via pre-commit).
[group('check')]
check: check-ruff check-deal check-pyright check-links

# Check Ruff rules without auto-fix.
[group('check')]
check-ruff *args:
  uv run ruff check --no-fix --statistics --output-format grouped {{args}}
  check-deal

# Check Deal lint rules.
[group('check'), private]
check-deal *args:
  uv run python -m deal lint {{args}}

# Check Ruff Bandit-derived 'S' rules.
[group('check')]
check-security *args:
  just check-ruff --select S {{args}}

# Check Pyright typing rules.
[group('check')]
check-pyright *args:
  uv run pyright {{args}}
# Soon: https://github.com/astral-sh/ruff/issues/3893

# Detect broken hyperlinks (via pre-commit).
[group('check')]
check-links:
  uv run pre-commit run markdown-link-check --hook-stage manual --all-files

###################################################################################################

# Run PyTest tests (except 'ux').
[group('test')]
test *args:
  uv run --locked pytest --no-cov -m "not ux" {{args}}

# Run PyTest tests not marked 'slow', 'net', or 'ux'.
[group('test')]
test-main *args:
  uv run pytest -m "not (slow or net or ux)" --tb=short {{args}}

# Run PyTest tests marked 'ux' (interaction or manual review).
[group('test')]
test-ux *args:
  uv run --locked pytest --no-cov -m ux {{args}}

# Run PyTest tests marked 'property', with Hypothesis "explain phase" enabled.
[group('test')]
test-property *args:
  uv run pytest -m property --hypothesis-explain --hypothesis-show-statistics --tb=short {{args}}

# Run PyTest tests (except 'ux') stepwise (starting with last failure).
[group('test')]
test-stepwise *args:
  uv run --locked pytest --no-cov -m "not ux" {{args}}

# Run PyTest tests marked 'ux' stepwise (starting with last failure).
[group('test')]
test-ux-stepwise *args:
  uv run --locked pytest --no-cov -m ux {{args}}

# Run PyTest tests (except 'ux'), showing minimal output.
[group('test')]
test-quietly *args:
  uv run --locked pytest --no-cov -m "not ux" --capture=no --tb=line {{args}}

# Run PyTest tests (except 'ux'), showing tracebacks, locals, and INFO.
[group('test')]
test-loudly *args:
  uv run --locked pytest --no-cov -m "not ux" --showlocals --full-trace --log-level INFO {{args}}

# Run PyTest tests with pdb debugger.
[group('test')]
test-with-pdb *args:
  uv run --locked pytest --no-cov --pdb {{args}}

# Run all PyTest tests, highlighting test durations.
[group('test')]
test-durations *args:
  uv run --locked pytest --no-cov --durations=0 --durations-min=0 {{args}}

# Run doctest tests (via PyTest).
[group('test')]
doctest *args:
  uv run --locked pytest --doctest-modules src/ {{args}}

# List PyTest fixtures.
[group('test')]
list-fixtures:
  uv run pytest --fixtures

###################################################################################################

# Build mkdocs docs from scratch, treating warnings as errors.
[group('docs')]
build-docs *args:
  uv run mkdocs build --clean --strict {{args}}

# Locally serve the mkdocs docs.
[group('docs')]
serve-docs *args:
  uv run mkdocs serve {{args}}

###################################################################################################

# `uv run --locked`.
[group('alias')]
run +args:
  uv run --locked {{args}}

# `uv run --locked python`.
[group('alias')]
python *args:
  uv run --locked python {{args}}

# `uv run --locked --module`.
[group('alias'), private]
call module *args:
  uv run --locked --script file {{args}}

# Runs the file as a PEP 723 script:
# `uv run --locked --script-file`.
[group('alias'), private]
script file *args:
  uv run --locked --script file {{args}}

# `uv run --locked pre-commit`.
[group('alias')]
pre-commit *args:
  uv run --locked pre-commit {{args}}

# `uv run --locked pre-commit run {hook}`.
[group('alias')]
hook name *args:
  uv run --locked pre-commit run name {{args}}

# `uv run --locked ruff`.
[group('alias')]
ruff *args:
  uv run --locked ruff {{args}}

# `uv run --locked pytest`.
[group('alias')]
pytest *args:
  uv run --locked pytest {{args}}

# `uv run --locked hypothesis fuzz`.
[group('alias')]
fuzz *args:
  uv run --locked hypothesis fuzz {{args}}

# `uv run --locked hypothesis codemod`.
[group('alias')]
codemod *args:
  uv run --locked hypothesis codemod {{args}}

# `uv run --locked hypothesis write`.
[group('alias')]
write-test *args:
  just _write_test {{args}}

# Private alias just so `="--help"` isn't shown in help.
_write_test *args="--help":
  uv run --locked --module hypothesis write {{args}}

# `uv run --locked --module deal`.
[group('alias')]
deal *args:
  just _deal {{args}}

# Private alias just so `="--help"` isn't shown in help.
_deal *args="--help":
  uv run --locked --module deal {{args}}

# `gh pr create --fill-verbose --web --draft`.
[group('alias')]
gh-pr *args:
  gh pr create --fill-verbose --web --draft {{args}}
