# https://github.com/casey/just
# https://cheatography.com/linux-china/cheat-sheets/justfile/

list:
    just --list --unsorted

###################################################################################################

# Delegate to `uv run --locked {}`.
run *args:
    uv --locked -- {{args}}

# Upgrade the lock file, sync the venv, and install pre-commit hooks.
prep:
    uv lock --refresh
    uv sync --only-dev
	uv run pre-commit install

# Upgrade pre-commit hooks.
upgrade-hooks:
    uv run pre-commit autoupdate
    uv run pre-commit gc

# Upgrade the lock file and sync the venv.
lock:
    uv lock --refresh
    uv sync --only-dev
alias sync := lock

# Remove temporary files.
clean:
    uv cache prune
    uv run pre-commit gc

# Upgrade the lock file, clean, and auto-fix+auto-format changes.
refresh: lock clean fix-changes format-changes

# Creates a pull request on GitHub using the GitHub CLI.
create-pr:
    gh pr create --fill --web --draft

###################################################################################################

# Format all files using Ruff and Prettier.
format-all:
    uv run pre-commit run --all-files ruff-format
	uv run pre-commit run --all-files prettier

# Format files with uncommitted changes using Ruff and Prettier.
format-changes:
    uv run pre-commit run ruff-format
	uv run pre-commit run prettier
alias format := format-changes

###################################################################################################

# Auto-fix Ruff rule violations in all files.
fix-all *args:
	uv run pre-commit run --all-files ruff {{args}}

# Auto-fix Ruff lint rule violations in all files with uncommitted changes.
fix-changes *args:
	uv run pre-commit run ruff {{args}}
alias fix := fix-changes

# Auto-fix Ruff lint rule violations using `--preview`, `--unsafe-fixes`, and `--ignore-noqa`.
fix-unsafe *args:
    uv run ruff check --preview --unsafe-fixes --fix-only {{args}}

###################################################################################################

# Find violations of Ruff lint and Pyright typing rules.
check: check-ruff check-pyright

# Find violations Ruff lint rules.
check-ruff *args:
	uv run ruff check --no-fix {{args}}

# Find violations of Bandit-derived `S` Ruff lint rules.
check-security *args:
    uv run ruff check --no-fix --select S {{args}}

# Find violations of Pyright typing rules.
check-pyright *args:
	uv run pyright {{args}}
# Soon: https://github.com/astral-sh/ruff/issues/3893

###################################################################################################

# Run all PyTest tests.
test *args:
	uv run pytest {{args}}

# Run PyTest tests that are not marked `slow`, `net`, or `ux`.
test-fast *args:
	uv run pytest -m 'not (slow or net or ux)' {{args}]}

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
