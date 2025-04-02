# https://github.com/casey/just
# https://cheatography.com/linux-china/cheat-sheets/justfile/

list:
  uv run pre-commit install
  just --list --unsorted

# Delegate to `uv run --locked {}`.
run *args:
  uv --locked -- {{args}}

###################################################################################################

# Upgrade the lock file, sync the venv, and install pre-commit hooks.
init:
  uv lock --upgrade
  uv sync --all-groups --all-extras --locked
  uv run pre-commit install --install-hooks --overwrite

# Upgrade the lock file, sync, clean, and fix and format changes.
refresh: lock bump-hooks fix-changes clean

# Auto-upgrade pre-commit hooks.
bump-hooks *args:
  uv run pre-commit autoupdate {{args}}
  uv run pre-commit gc

# Upgrade the lock file and sync the venv.
lock:
  uv sync --upgrade --all-groups --all-extras

# Sync the venv. Includes all groups and all extras. Installs the project as editable.
sync:
  uv sync --all-groups --all-extras

# Remove temporary files, including unlinked uv cache files and old Git hooks.
clean:
  uv cache prune
  uv run pre-commit gc

###################################################################################################

# Run pre-commit hooks on all files.
fix-all:
  uv run pre-commit run --all-files

# Run pre-commit hooks on all files with uncommitted changes.
fix-changes:
  uv run pre-commit run
alias fix := fix-changes

# Auto-fix Ruff violations.
fix-ruff *args:
  uv run ruff check --fix-only --output-format grouped {{args}}

# Auto-fix Ruff violations using `--preview`, `--unsafe-fixes`, and `--ignore-noqa`.
fix-ruff-unsafe *args:
  uv run ruff check --fix-only --output-format grouped --preview --unsafe-fixes --ignore-noqa {{args}}

###################################################################################################

# Find violations of Ruff lint and Pyright typing rules.
check: check-ruff check-pyright check-links

# Find violations of Ruff lint rules.
check-ruff *args:
  uv run ruff check --no-fix --output-format concise {{args}}

# Find violations of Bandit-derived `S` Ruff lint rules.
check-bandit *args:
  uv run ruff check --no-fix --output-format concise --select S {{args}}

# Find violations of Pyright typing rules.
check-pyright *args:
  uv run pyright {{args}}
# Soon: https://github.com/astral-sh/ruff/issues/3893

# Find broken hyperlinks in Markdown docs.
check-links *args:
  uv run pre-commit run markdown-link-check {{args}}

###################################################################################################

# Run all PyTest tests.
test-all *args:
  uv run pytest {{args}}

# Run PyTest tests that are not marked `slow`, `net`, or `ux`.
test-fast *args:
  uv run pytest -m 'not (slow or net or ux)' {{args}}

# List PyTest markers.
test-markers *args:
  uv run pytest --markers

###################################################################################################

# Build the docs, failing for any warnings.
docs-build *args:
  uv run mkdocs build --clean --strict {{args}}

# Locally serve the docs.
docs-serve *args:
  uv run mkdocs serve {{args}}

###################################################################################################

# Opens a pull request on GitHub using the GitHub CLI.
open-pr *args:
  gh pr create --fill-verbose --web --draft {{args}}
