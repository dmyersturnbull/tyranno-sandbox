# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

# https://github.com/casey/just
# https://cheatography.com/linux-china/cheat-sheets/justfile/

list:
  just --list --unsorted
alias help := list

# Initialize the project: sync the venv and install pre-commit hooks.
init:
  uv sync --all-extras
  uv run pre-commit install --install-hooks --overwrite

# Alias of `uv run --locked {}`.
run *args:
  uv --locked run {{args}}

# Open a pull request on GitHub (`gh pr create ...`).
open-pr *args:
  gh pr create --fill-verbose --web --draft {{args}}

###################################################################################################

# Upgrade depenencies and pre-commit hooks, sync, reformat (tidy), and prune.
[group('project')]
refresh: bump tidy prune

# Bump dependencies and pre-commit hooks.
[group('project')]
bump *args:
  uv lock --upgrade
  uv run pre-commit autoupdate {{args}}
  uv run pre-commit gc

# (Hidden.) Auto-upgrade pre-commit hooks (`pre-commit autoupdate ...`).
[group('project')]
_bump-hooks *args:
  uv run pre-commit autoupdate {{args}}
  uv run pre-commit gc

# Remove unlinked uv cache files and old Git hooks.
[group('project')]
prune:
  uv cache prune
  uv run pre-commit gc

# Sync the venv with all extras and the 'dev' group.
[group('project')]
sync:
  uv sync --all-extras

# Upgrade the lock file and sync the venv.
[group('project')]
lock:
  uv sync --upgrade --all-extras

###################################################################################################

# Run pre-commit hooks on modified files (`pre-commit run ...`).
[group('tidy')]
tidy:
  uv run pre-commit run

# Run pre-commit hooks on ALL files.
[group('tidy')]
tidy-all:
  uv run pre-commit run --all-files

# Run Ruff formatter and Prettier on files with uncommitted changes.
[group('tidy')]
format:
  uv run pre-commit run ruff-format
  uv run pre-commit run prettier

# Run Ruff formatter and Prettier on all files.
[group('tidy')]
format-all:
  uv run pre-commit run ruff-format --all-files
  uv run pre-commit run prettier --all-files

# Fix Ruff rules (`ruff check ...`).
[group('tidy')]
ruff-fix *args:
  uv run ruff check --fix-only --output-format grouped {{args}}

# Fix Ruff preview and unsafe rules, ignoring 'noqa' (`ruff check ...`).
[group('tidy')]
ruff-fix-unsafe *args:
  uv run ruff check --fix-only --output-format grouped --preview --unsafe-fixes --ignore-noqa {{args}}

###################################################################################################

# Checks Ruff and Pyright rules.
[group('lint')]
lint: lint-ruff lint-pyright lint-links

# Checks Ruff rules (`ruff check ...`).
[group('lint')]
lint-ruff *args:
  uv run ruff check --no-fix --output-format concise {{args}}

# Checks Bandit-derived 'S' (security) rules (`ruff check ...`).
[group('lint')]
lint-bandit *args:
  uv run ruff check --no-fix --output-format concise --select S {{args}}

# Find violations of Pyright typing rules (`pyright ...`).
[group('lint')]
lint-pyright *args:
  uv run pyright {{args}}
# Soon: https://github.com/astral-sh/ruff/issues/3893

# Find broken hyperlinks in Markdown docs (`pre-commit run markdown-link-check ...`).
[group('lint')]
lint-links *args:
  uv run pre-commit run markdown-link-check {{args}}

###################################################################################################

# Run all PyTest tests (`pytest ...`).
[group('test')]
test *args:
  uv run pytest {{args}}

# Run PyTest tests not marked 'slow', 'net', or 'ux' (`pytest ...`).
[group('test')]
test-fast *args:
  uv run pytest -m "not (slow or net or ux)" {{args}}

# List PyTest markers.
[group('test')]
list-test-markers:
  uv run pytest --markers

###################################################################################################

# Build the docs, failing on warnings (`mkdocs build ...`).
[group('docs')]
build-docs *args:
  uv run mkdocs build --clean --strict {{args}}

# Locally serve the docs (`mkdocs serve ...`).
[group('docs')]
serve-docs *args:
  uv run mkdocs serve {{args}}

###################################################################################################

# (Hidden.) Alias of `uv run {}`.
[group('alias')]
_run-synced *args:
  uv run {{args}}

# (Hidden.) Alias of `uv run --no-sync {}`.
[group('alias')]
_run-unsynced *args:
  uv --no-sync run {{args}}

# (Hidden.) Alias of `uv run python {}`.
[group('alias')]
_python *args:
  uv run python {{args}}

# (Hidden.) Alias of `uv run pre-commit {}`.
[group('alias')]
_pre-commit *args:
  uv run pre-commit {{args}}

# (Hidden.) Alias of `uv run ruff {}`.
[group('alias')]
_ruff *args:
  uv run ruff {{args}}

# (Hidden.) Alias of `uv run pytest {}`.
[group('alias')]
_pytest *args:
  uv run pytest {{args}}
