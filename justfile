# https://github.com/casey/just
# https://cheatography.com/linux-china/cheat-sheets/justfile/

list:
  uv run pre-commit install
  just --list --unsorted

# Delegate to `uv run --locked {}` (args → `uv run`).
run *args:
  uv --locked run {{args}}

###################################################################################################

# Upgrade the lock file, sync the venv, and install pre-commit hooks.
init:
  uv lock --upgrade
  uv sync --all-extras --locked
  uv run pre-commit install --install-hooks --overwrite

# Upgrade the lock file, sync, clean, and fix and format changes.
refresh: lock bump-hooks fix-changes clean

# Auto-upgrade pre-commit hooks (args → `pre-commit autoupdate`).
bump-hooks *args:
  uv run pre-commit autoupdate {{args}}
  uv run pre-commit gc

# Upgrade the lock file and sync the venv.
lock:
  uv sync --upgrade --all-extras

# Sync the venv with all extras and the 'dev' group.
sync:
  uv sync --all-extras

# Remove temporary files, including unlinked uv cache files and old Git hooks.
clean:
  uv cache prune
  uv run pre-commit gc

###################################################################################################

# Run Ruff formatter and Prettier on all files.
format-all:
  uv run pre-commit run ruff-format --all-files
  uv run pre-commit run prettier --all-files

# Run Ruff formatter and Prettier on files with uncommitted changes.
format-changes:
  uv run pre-commit run ruff-format
  uv run pre-commit run prettier
alias format := fix-changes

###################################################################################################

# Run pre-commit hooks on all files.
fix-all:
  uv run pre-commit run --all-files

# Run pre-commit hooks on files with uncommitted changes.
fix-changes:
  uv run pre-commit run
alias fix := fix-changes

###################################################################################################

# Auto-fix Ruff violations (args → `ruff check`).
fix-ruff *args:
  uv run ruff check --fix-only --output-format grouped {{args}}

# Run with `--preview`, `--unsafe-fixes`, and `--ignore-noqa` (args → `ruff check`).
fix-ruff-unsafe *args:
  uv run ruff check --fix-only --output-format grouped --preview --unsafe-fixes --ignore-noqa {{args}}

###################################################################################################

# Find violations of Ruff lint and Pyright typing rules.
check: check-ruff check-pyright check-links

# Find violations of Ruff rules (args → `ruff check`).
check-ruff *args:
  uv run ruff check --no-fix --output-format concise {{args}}

# Find violations of Bandit-derived `S` (security) Ruff rules (args → `ruff check`).
check-bandit *args:
  uv run ruff check --no-fix --output-format concise --select S {{args}}

# Find violations of Pyright typing rules (args → `pyright`).
check-pyright *args:
  uv run pyright {{args}}
# Soon: https://github.com/astral-sh/ruff/issues/3893

# Find broken hyperlinks in Markdown docs (args → `pre-commit run markdown-link-check`).
check-links *args:
  uv run pre-commit run markdown-link-check {{args}}

###################################################################################################

# Run all PyTest tests (args → `pytest`).
test-all *args:
  uv run pytest {{args}}

# Run PyTest with `-m 'not (slow or net or ux)'` (args → `pytest`).
test-fast *args:
  uv run pytest -m 'not (slow or net or ux)' {{args}}

# List PyTest markers.
test-markers:
  uv run pytest --markers

###################################################################################################

# Build the docs, failing for any warnings (args → `mkdocs build`).
docs-build *args:
  uv run mkdocs build --clean --strict {{args}}

# Locally serve the docs (args → `mkdocs serve`).
docs-serve *args:
  uv run mkdocs serve {{args}}

###################################################################################################

# Opens a pull request on GitHub (args → `gh pr create`).
open-pr *args:
  gh pr create --fill-verbose --web --draft {{args}}
