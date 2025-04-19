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
  @just --list --unsorted
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
revamp: bump-lock bump-hooks fix-changes format-changes clean

# Lock and sync the venv exactly with all extras.
[group('project')]
sync:
  uv sync --all-extras --exact

# Update pre-commit hooks, update the lock file, and sync the venv.
[group('project')]
bump: bump-lock bump-hooks

# Update the lock file and sync the venv.
[group('project')]
bump-lock:
  uv sync --upgrade --all-extras --exact
  uv run pre-commit gc

# Auto-update commit hooks.
[group('project')]
bump-hooks:
  uv run pre-commit autoupdate
  uv run pre-commit gc

# Remove temporary files.
[group('project')]
clean: && trash
  uv cache prune
  uv run pre-commit gc

# Delete temporary project files and directories.
[group('project'), private]
@trash:
  - rm .coverage.json
  - rm -r .ruff_cache/
  - rm -r .hypothesis/
  - rm -r **/__pycache__/
  - rm -r **/.pytest_cache/
  - rm -r **/cython_debug/
  - rm -r **/*.egg-info/
  - rm **/*.py[codi]

# Delete files whose names indicate they're temporary.
[group('project'), private]
@trash-unsafe:
  - rm **/.DS_Store
  - rm **/Thumbs.db
  - rm **/*.tmp
  - rm **/*.temp
  - rm **/*.swp
  - rm **/.#*
  - rm **/*[~\$]
  - rm **/*.directory

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

# Run all PyTest tests.
[group('test')]
test-full *args:
  uv run pytest {{args}}
alias test := test-full

# Run PyTest tests not marked 'slow', 'net', or 'ux'.
[group('test')]
test-fast *args:
  uv run pytest -m "not (slow or net or ux)" {{args}}

# Run PyTest tests marked 'property', with Hypothesis explain phase enabled.
[group('test')]
test-property *args:
  uv run pytest -m "property" --hypothesis-explain {{args}}

# Run PyTest tests with verbose options.
[group('test')]
test-debug *args:
  uv run pytest \
    --full-trace \
    --showlocals \
    --hypothesis-explain \
    --log-level DEBUG \
    {{args}}

# Run tests with verbose options and stepwise mode.
[group('test')]
test-stepwise *args: (test-debug "--no-cov" "--stepwise" args)

# Run PyTest tests with pdb debugger.
[group('test')]
test-pdb *args:
  uv run pytest --no-cov --pdb {{args}}

# Run PyTest tests and highlight test durations.
[group('test')]
test-durations *args:
  uv run pytest --quiet --log-level WARNING --durations=0 --durations-min=0.0 {{args}}

# Run doctest tests through PyTest.
[group('test')]
doctest *args:
  uv run pytest --doctest-modules src/ {{args}}

# Show available PyTest fixtures and their associated tests.
[group('test')]
show-test-fixtures:
  uv run pytest --setup-plan

# Show available PyTest markers.
[group('test')]
show-test-markers:
  uv run pytest --markers

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
