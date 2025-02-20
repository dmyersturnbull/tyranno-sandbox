# https://github.com/casey/just
# https://cheatography.com/linux-china/cheat-sheets/justfile/

default:
    just --list --unsorted

# Install pre-commit hooks.
install-hooks:
	uv run --frozen pre-commit install

###############################################################################

# Upgrade the lock file and sync.
lock:
    uv lock --upgrade
    uv sync --only-dev

# Sync .venv to the dev group dependencies in uv.lock.
sync:
    uv sync --only-dev

###############################################################################

# Auto-fix and format all files with Ruff and Prettier.
format-all *args:
	uv run --frozen pre-commit run --all-files ruff {{args}}
	uv run --frozen pre-commit run --all-files ruff-format {{args}}
	uv run --frozen pre-commit run --all-files prettier {{args}}

# Auto-fix and format files with uncommitted changes.
format-changes *args:
	uv run --frozen pre-commit run ruff {{args}}
	uv run --frozen pre-commit run ruff-format {{args}}
	uv run --frozen pre-commit run prettier {{args}}
alias format := format-changes

###############################################################################

# Check code quality with Ruff and Pyright (doesn't fix).
check: check-ruff check-pyright

# Check Ruff lint rules (doesn't fix).
check-ruff *args:
	uv run --frozen ruff check --no-fix {{args}}

# Check Bandit-derived Ruff `S` lint rules (doesn't fix).
check-security:
    uv run --frozen ruff check --no-fix --select S

# Check typing with Pyright.
check-pyright *args:
	uv run --frozen pyright {{args}}
# Soon: https://github.com/astral-sh/ruff/issues/3893

###############################################################################

# Run all PyTest tests.
test-all: test-unit test-slow test-net test-ux

# Run PyTest tests that are not marked `slow`, `net`, or `ux`.
test:
	uv run --frozen pytest -m 'not (slow or net or ux)'

# Run PyTest tests marked `slow`.
test-slow:
	uv run --frozen pytest -m slow

# Run PyTest tests marked `net` (those requiring network access).
test-net:
	uv run --frozen pytest -m net

# Run PyTest tests marked `ux` (those requiring manual validation).
test-ux:
	uv run --frozen pytest -m ux

###############################################################################

# Build the docs, failing for any warnings.
docs-build *args:
    uv run --frozen mkdocs build --clean --strict {{args}}

# Locally serve the docs.
docs-serve *args:
    uv run mkdocs serve {{args}}
