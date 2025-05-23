# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

# https://github.com/casey/just
# https://just.systems/man/en/
# https://cheatography.com/linux-china/cheat-sheets/justfile/

set ignore-comments	:= true

git_sha := `git rev-parse --short=16 HEAD`
git_ref := `git rev-parse --abbrev-ref HEAD`
git_rev_date := `git --no-pager log -1 --format=%cd`

###################################################################################################

# List available recipes.
[group('help')]
list:
  @just --list --unsorted
alias help := list

# Print info for a bug report.
[group('help')]
info:
  @echo "os: {{os()}}"
  @echo "cpu_arch: {{arch()}}"
  @echo "cpu_count: {{num_cpus()}}"
  @echo "shell: {{env('SHELL', '?')}}"
  @echo "lang: {{env('LANG', '?')}}"
  @echo "repo: {{file_name(justfile_directory())}}"
  @echo "git_ref: {{git_ref}}"
  @echo "git_sha: {{git_sha}}"
  @echo "git_rev: {{git_rev_date}}"

###################################################################################################

# Sync the venv and install commit hooks.
[group('setup')]
init:
  uv sync --all-extras --exact
  uv run pre-commit install --install-hooks --overwrite
  uv run pre-commit gc

###################################################################################################

# `update`, `fix-changes`, `format-changes`, `clean`.
[group('project')]
revamp: update fix-changes format-changes clean

# Lock and sync the venv with all extras.
[group('project')]
sync:
  uv sync --all-extras --exact
alias lock := sync

# `update-lock`, `update-hooks`.
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

# Prune temp data, including from uv, pre-commit, and git.
[group('project')]
clean: delete-temp clean-main clean-git

# Delete unused uv and pre-commit cache data. (Called by `clean`.)
[group('project'), private]
clean-main:
  uv run pre-commit gc
  uv cache prune

# Start incremental 'git maintenance' tasks. (Called by 'clean'.)
[group('project'), private]
clean-git:
  git maintenance run \
    --task=commit-graph \
    --task=prefetch \
    --task=loose-objects \
    --task=incremental-repack \
    --task=pack-refs

# Delete cache and other temporary data.
[group('project'), private]
delete-temp:
  # Generated docs:
  - rm -f -r .site/
  # Python temp files:
  - rm -f -r .ruff_cache/
  - rm -f -r .hypothesis/
  - rm -f -r **/__pycache__/
  - rm -f -r **/.pytest_cache/
  - rm -f -r **/cython_debug/
  - rm -f -r **/*.egg-info/
  - rm -f -r **/.node-modules/
  - rm -f .coverage.json
  - rm -f **/*.py[codi]
  # OS-specific files:
  - rm -f **/.directory
  - rm -f **/.DS_Store
  - rm -f **/.localized
  - rm -f **/Thumbs.db

# Delete files whose names indicate they're temporary. [CAUTION]
[group('project'), private]
@delete-probable-temp:
  # Log files directly in `/`, `src/`, or `tests/`
  - rm -f *.log
  - rm -f src/*.log
  - rm -f tests/*.log
  # Directories named exactly `.(bak|junk|temp|tmp|trash)`
  - rm -f -r **/.bak
  - rm -f -r **/.junk
  - rm -f -r **/.temp
  - rm -f -r **/.tmp
  - rm -f -r **/.trash
  # Files with extensions `.(bak|junk|temp|tmp|trash|swp)`
  - rm -f **/*.bak
  - rm -f **/*.junk
  - rm -f **/*.temp
  - rm -f **/*.tmp
  - rm -f **/*.trash
  - rm -f **/*.swp
  # Files starting or end with `~|#|$` (or starting with `.~`).
  - rm -f **/[~#\$]*
  - rm -f **/*[~#\$]
  - rm -f **/.~*

# NOTE: "Advanced" or "optional" recipe, unlisted but invoked directly.
# Run 'git remote prune --all' and start 'git maintenance run gc'. [CAUTION]
[group('project'), private]
prune-git:
  # Needed on macOS.
  @- chflags -R nouchg .git/*
  # Prune tracked refs first because it's a foreground task.
  git remote prune --all
  # Uses 'gc.pruneExpire'.
  git maintenance run --task gc

# NOTE: "Advanced" or "optional" recipe, unlisted but invoked directly.
# Minify the repo by deleting nearly all recreatable files. [CAUTION]
[group('project'), private]
minify-repo: clean delete-probable-temp
  uv run pre-commit clean
  uv run pre-commit uninstall
  - rm -f -r .venv
  - rm -f -r .idea
  - rm -f uv.lock

###################################################################################################

# Format modified files (pre-commit).
[group('format')]
format-changes: _format
alias format := format-changes

# Format ALL files (pre-commit).
[group('format')]
format-all: (_format "--all-files")

# <Internal.>
_format *args:
  - uv run pre-commit run end-of-file-fixer {{args}}
  - uv run pre-commit run fix-byte-order-marker {{args}}
  - uv run pre-commit run trailing-whitespace {{args}}
  - uv run pre-commit run ruff-format {{args}}
  - uv run pre-commit run prettier {{args}}

###################################################################################################

# Ruff auto-fix modified files (pre-commit).
[group('fix'), no-exit-message]
fix-changes:
  git add .pre-commit-config.yaml
  uv run pre-commit run ruff-check
alias fix := fix-changes

# Ruff auto-fix ALL files (pre-commit).
[group('fix'), no-exit-message]
fix-all:
  git add .pre-commit-config.yaml
  uv run pre-commit run ruff-check --all-files

# Ruff auto-fix rule violations.
[group('fix'), no-exit-message]
fix-ruff *args="--show-fixes": (_fix_ruff args)

# Ruff auto-fix, including unsafe fixes. [CAUTION]
[group('fix'), no-exit-message]
fix-ruff-unsafe *args="--show-fixes": (_fix_ruff "--unsafe-fixes" args)

# <Internal.>
[no-exit-message]
_fix_ruff *args:
  uv run ruff check --fix-only --output-format grouped {{args}}

###################################################################################################

# Check basic rules (pre-commit).
[group('check')]
check-simple:
  # Keep slower hooks lower in the list.
  uv run --no-sync pre-commit run check-filenames
  uv run --no-sync pre-commit run check-symlinks
  uv run --no-sync pre-commit run check-case-conflict
  uv run --no-sync pre-commit run check-illegal-windows-names
  uv run --no-sync pre-commit run check-shebang-scripts-are-executable
  uv run --no-sync pre-commit run check-github-actions
  uv run --no-sync pre-commit run check-github-workflows
  uv run --no-sync pre-commit run check-compose-spec
  uv run --no-sync pre-commit run forbid-new-submodules
  uv run --no-sync pre-commit run trailing-whitespace
  uv run --no-sync pre-commit run check-added-large-files

# Check Ruff rules without auto-fix.
[group('check'), no-exit-message]
check-ruff *args:
  uv run --no-sync ruff check --no-fix --output-format grouped {{args}}

# Check Ruff Bandit-derived 'S' rules.
[group('check'), no-exit-message]
check-bandit *args: (check-ruff "--select" "S" args)

# Check Astral's ty typing rules.
[group('check'), no-exit-message]
check-ty *args:
  uv run --no-sync ty check {{args}}

# Detect broken hyperlinks (pre-commit).
[group('check'), no-exit-message]
check-links:
  uv run --no-sync pre-commit run markdown-link-check --hook-stage manual --all-files

###################################################################################################

# Run tests NOT marked 'ux'.
[group('test'), no-exit-message]
test-non-ux *args: (_with_cov "-m" "not ux" args)

# Run tests marked 'ux' (manual interaction or verification).
[group('test'), no-exit-message]
test-ux *args: (_no_cov "-m" "ux" args)

# Run tests NOT marked 'ux', 'e2e', 'slow', or 'net'.
[group('test'), no-exit-message]
test-simple *args: (_with_cov "-m" "not (ux or e2e or slow or net)" args)

# Run tests marked 'property' with Hypothesis options.
[group('test'), no-exit-message]
test-property *args: (_no_cov "-m" "property" "--hypothesis-explain" "--hypothesis-show-statistics" args)

# Run all PyTest tests stepwise (starting at last failure).
[group('test'), no-exit-message]
test-stepwise *args: (_no_cov "--stepwise" args)

# Run all PyTest tests, highlighting test durations.
[group('test'), no-exit-message]
test-durations *args: (_no_cov "--durations=0" "--durations-min=0" args)

# Run doctest tests (via PyTest).
[group('test'), no-exit-message]
doctest *args: (_no_cov "--doctest-modules" "src/" args)

# Run all PyTest tests, showing minimal output.
[group('test'), no-exit-message, private]
test-quietly *args: (_no_cov "--capture=no" "--tb=line" args)

# Run all PyTest tests, showing tracebacks, locals, and INFO.
[group('test'), no-exit-message, private]
test-loudly *args: (_no_cov "--showlocals" "--full-trace" "--log-level=INFO" args)

# Run all PyTest tests with pdb debugger.
[group('test'), no-exit-message, private]
test-with-pdb *args: (_no_cov "--pdb" args)

# <Internal.>
[no-exit-message]
_no_cov *args:
  uv run --locked pytest --no-cov {{args}}

# <Internal.>
[no-exit-message]
_with_cov *args: (pytest args)

###################################################################################################

# Build mkdocs docs from scratch, failing for warnings.
[group('docs'), no-exit-message]
build-docs *args:
  uv run --locked mkdocs build --clean --strict {{args}}

# Locally serve the mkdocs docs.
[group('docs'), no-exit-message]
serve-docs *args:
  uv run mkdocs serve {{args}}

###################################################################################################

# `uv run --locked`.
[group('alias'), no-exit-message]
run +args:
  uv run --locked {{args}}

# `uv run --locked python`.
[group('alias'), no-exit-message]
python *args:
  uv run --locked python {{args}}

# `uv run --locked pre-commit`.
[group('alias'), no-exit-message]
pre-commit *args:
  uv run --locked pre-commit {{args}}

# `uv run --locked pre-commit run {hook}`.
[group('alias'), no-exit-message]
hook name *args:
  uv run --locked pre-commit run {{name}} {{args}}

# `uv run --locked ruff`.
[group('alias'), no-exit-message]
ruff *args:
  uv run --locked ruff {{args}}

# `uv run --locked pytest`.
[group('alias'), no-exit-message]
pytest *args:
  uv run --locked pytest {{args}}

# `gh pr create --fill-verbose --web --draft`.
[group('alias'), no-exit-message]
pr *args:
  gh pr create --fill-verbose --web --draft {{args}}
