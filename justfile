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
[group('setup')]
init:
  uv sync --all-extras --exact
  uv run --no-sync pre-commit install --install-hooks --overwrite
  uv run --no-sync pre-commit gc

# Update the lock file, sync the venv, auto-fix + format changes, and clean.
[group('project')]
revamp: update fix-changes format-changes clean

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
  uv run --no-sync pre-commit gc
alias upgrade-lock := update-lock

# Auto-update commit hooks.
[group('project')]
update-hooks:
  uv run pre-commit autoupdate
  uv run --no-sync pre-commit gc
alias upgrade-hooks := update-hooks

# This is an alternative to 'git gc':
# Spawns incremental optimization tasks in background via 'git maintenance'.
[group('project'), private]
maintain-git:
  git maintenance run \
    --task=commit-graph \
    --task=prefetch \
    --task=loose-objects \
    --task=incremental-repack \
    --task=pack-refs

# Minify the repo by deleting nearly all recreatable files (UNSAFE).
[group('project'), private]
strip-down-repo: clean (prune-git "1.hour") && delete-unsafe _pkg_idea
  uv run --no-sync pre-commit clean
  uv run --no-sync pre-commit uninstall
  - rm -f -r .venv
  - rm -f uv.lock

# Package .idea (will fail if the directory does not exist).
[group('project')]
_pkg_idea:
  @tar -c -z -f idea.tar.gz .idea
  @rm -r .idea/
  @echo "Wrote idea.tar.gz"

# Remove temporary files and most caches.
[group('project')]
clean: && delete-trash
  uv run --no-sync pre-commit gc
  uv cache prune

# Runs 'git gc --prune={prune}' and 'git remote prune --all'.
[group('project'), private]
prune-git prune='2.week':
  # Needed on macOS (fails on others).
  @- chflags -R nouchg .git/*
  git gc --prune={{prune}}
  git remote prune --all

# Delete temporary project files and directories.
[group('project'), private]
delete-trash:
  - rm -f -r .ruff_cache/
  - rm -f -r .hypothesis/
  - rm -f -r **/__pycache__/
  - rm -f -r **/.pytest_cache/
  - rm -f -r **/cython_debug/
  - rm -f -r **/*.egg-info/
  - rm -f -r **/.node-modules/
  - rm -f -r .site/
  - rm -f .coverage.json
  - rm -f **/*.py[codi]
  # Use `-` for the rare case that neither Linux nor macOS nor Windows applies.
  @- just _trash_os_specific

[group('project'), linux]
_trash_os_specific:
  - rm -f **/.directory

[group('project'), macos]
_trash_os_specific:
  - rm -f **/.DS_Store
  - rm -f **/.localized

[group('project'), windows]
_trash_os_specific:
  - rm -f **/Thumbs.db

# Delete files whose names indicate they're temporary (UNSAFE).
[group('project'), private]
@delete-unsafe:
  - rm -f -r .trash
  - rm -f *.log
  - rm -f src/**/*.log
  - rm -f tests/*.log
  - rm -f **/*.pid
  - rm -f **/*.tmp
  - rm -f **/*.temp
  - rm -f **/*.swp
  - rm -f **/*.bak
  - rm -f **/.#*
  - rm -f **/*[~\$]

###################################################################################################

# Format modified files (via pre-commit).
[group('format')]
format-changes: _format
alias format := format-changes

# Format ALL files (via pre-commit).
[group('format')]
format-all: (_format "--all-files")

_format *args:
  uv sync
  - uv run --no-sync pre-commit run end-of-file-fixer {{args}}
  - uv run --no-sync pre-commit run fix-byte-order-marker {{args}}
  - uv run --no-sync pre-commit run trailing-whitespace {{args}}
  - uv run --no-sync pre-commit run ruff-format {{args}}
  - uv run --no-sync pre-commit run prettier {{args}}

###################################################################################################

# Fix configured Ruff rule violations in modified files (via pre-commit).
[group('fix')]
fix-changes:
  git add .pre-commit-config.yaml
  - uv run pre-commit run ruff
  git add .pre-commit-config.yaml
  uv run --no-sync pre-commit run ruff
alias fix := fix-changes

# Fix configured Ruff rule violations in ALL files (via pre-commit).
[group('fix')]
fix-all:
  git add .pre-commit-config.yaml
  - uv run pre-commit run ruff --all-files
  git add .pre-commit-config.yaml
  uv run --no-sync pre-commit run ruff --all-files

# Fix configured Ruff rule violations.
[group('fix')]
fix-ruff *args: (_fix_ruff args)

# Fix Ruff rule violations, including preview, unsafe, and noqa-suppressed.
[group('fix')]
fix-ruff-unsafe *args: (_fix_ruff "--preview" "--unsafe-fixes" "--ignore-noqa" args)

_fix_ruff *args:
  - uv run ruff check --fix-only --show-fixes --output-format grouped {{args}}

###################################################################################################

# Check basic rules (via pre-commit).
[group('check')]
check *args:
  uv sync
  uv run --no-sync pre-commit run check-filenames
  uv run --no-sync pre-commit run check-symlinks
  uv run --no-sync pre-commit run check-case-conflict
  uv run --no-sync pre-commit run check-illegal-windows-names
  uv run --no-sync pre-commit run check-shebang-scripts-are-executable

# Check JSON and YAML files against known schemas (via pre-commit).
[group('check')]
check-schemas *args:
  uv sync
  uv run --no-sync pre-commit run check-github-workflows
  uv run --no-sync pre-commit run check-compose-spec

# Check Ruff rules without auto-fix.
[group('check')]
check-ruff *args:
  uv run ruff check --no-fix --output-format grouped {{args}}

# Check Ruff Bandit-derived 'S' rules.
[group('check')]
check-bandit *args:
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

# Run PyTest tests (except 'ux' and 'e2e').
[group('test')]
test *args:
  uv run --locked pytest --no-cov -m "not (ux or e2e)" {{args}}

# Run PyTest tests not marked 'slow', 'net', 'ux', or 'e2e'.
[group('test')]
test-main *args:
  uv run --locked pytest -m "not (slow or net or ux or e2e)" {{args}}

# Run PyTest tests marked 'ux' (interaction or manual review).
[group('test')]
test-ux *args:
  uv run --locked pytest --no-cov -m ux {{args}}

# Run PyTest tests marked 'property' with extra Hypothesis options.
[group('test')]
test-property *args:
  uv run --locked pytest -m property --hypothesis-explain --hypothesis-show-statistics {{args}}

# Run all PyTest tests stepwise (starting at last failure).
[group('test')]
test-stepwise *args:
  uv run --locked pytest --no-cov {{args}}

# Run all PyTest tests, highlighting test durations.
[group('test')]
test-durations *args:
  uv run --locked pytest --no-cov --durations=0 --durations-min=0 {{args}}

# Run doctest tests (via PyTest).
[group('test')]
doctest *args:
  uv run --locked pytest --doctest-modules src/ {{args}}

# Run all PyTest tests, showing minimal output.
[group('test'), private]
test-quietly *args:
  uv run --locked pytest --no-cov --capture=no --tb=line {{args}}

# Run all PyTest tests, showing tracebacks, locals, and INFO.
[group('test'), private]
test-loudly *args:
  uv run --locked pytest --no-cov --showlocals --full-trace --log-level INFO {{args}}

# Run all PyTest tests with pdb debugger.
[group('test'), private]
test-with-pdb *args:
  uv run --locked pytest --no-cov --pdb {{args}}

###################################################################################################

# Build mkdocs docs from scratch, treating warnings as errors.
[group('docs')]
build-docs *args:
  uv run --locked mkdocs build --clean --strict {{args}}

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

# `gh pr create --fill-verbose --web --draft`.
[group('alias')]
pr *args:
  gh pr create --fill-verbose --web --draft {{args}}
