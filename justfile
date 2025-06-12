# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
# https://github.com/casey/just
# https://just.systems/man/en/
# https://cheatography.com/linux-china/cheat-sheets/justfile/
# CAUTION – Quotes aren't quotes.
# This doesn't do what you'd expect:
# ```
# git +args:
#   git {{args}}
# commit-reformat: (git "-m" "style: reformat code")
# ```
# This results in `git -m style: reformat code` !

set dotenv-load := true
set ignore-comments := true

# Confusingly, Python has a default warning filter, which is **different** from `-W default`.

export PYTHONWARNINGS := env('PYTHONWARNINGS', 'default')

# Enable dev mode (https://docs.python.org/3/library/devmode.html):

export PYTHONDEVMODE := env('PYTHONDEVMODE', '1')

# To complain when `encoding=` is omitted (in addition to Ruff rule):
# export PYTHONWARNDEFAULTENCODING := env('PYTHONWARNDEFAULTENCODING', '1')

git_sha := `git rev-parse --short=16 HEAD`
git_ref := `git rev-parse --abbrev-ref HEAD`
git_rev_date := `git --no-pager log -1 --format=%cd`

###################################################################################################

# List available recipes.
[group('help')]
list:
    @just --list --unsorted --list-prefix "  "

alias help := list

# Print info for a bug report.
[group('help')]
info:
    @echo "os: {{ os() }}"
    @echo "cpu_arch: {{ arch() }}"
    @echo "cpu_count: {{ num_cpus() }}"
    @echo "shell: {{ env('SHELL', '?') }}"
    @echo "lang: {{ env('LANG', '?') }}"
    @echo "repo_dir: {{ file_name(justfile_directory()) }}"
    @echo "project_name: {{ replace_regex(`uv version`, ' .+', '') }}"
    @echo "project_ver: {{ `uv version --short` }}"
    @echo "git_ref: {{ git_ref }}"
    @echo "git_sha: {{ git_sha }}"
    @echo "git_rev: {{ git_rev_date }}"

###################################################################################################

# Sync the venv and install commit hooks.
[group('setup')]
init:
    uv sync --all-extras --exact
    uv run pre-commit install --install-hooks --overwrite
    uv run pre-commit gc

###################################################################################################

# `just update fix-changes format-changes clean`
[group('project')]
spruce: update fix-changes format-changes clean

# `just update-lock update-hooks`
[group('project')]
update: update-lock update-hooks

alias upgrade := update

# Update the lock file and sync the venv.
[group('project')]
update-lock: sync
    uv run pre-commit gc

alias upgrade-lock := update-lock

# Auto-update commit hooks.
[group('project')]
update-hooks:
    uv run --locked pre-commit autoupdate
    uv run --no-sync pre-commit gc

alias upgrade-hooks := update-hooks

# Lock and sync the venv (uses all extras).
[group('project')]
sync:
    uv sync --all-extras --exact

alias lock := sync

# Prune temp data, including from uv, pre-commit, and git.
[group('project')]
clean: delete-temp clean-main clean-git

# Delete unused uv and pre-commit cache data. (Called by `clean`.)
[group('project')]
[private]
clean-main:
    uv run --no-sync pre-commit gc
    uv cache prune

# Start incremental 'git maintenance' tasks. (Called by 'clean'.)
[group('project')]
[private]
clean-git:
    git maintenance run \
      --task=commit-graph \
      --task=prefetch \
      --task=loose-objects \
      --task=incremental-repack \
      --task=pack-refs

# Delete cache and other temporary data.
[group('project')]
[private]
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
[group('project')]
[private]
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
[group('project')]
[private]
prune-git:
    # Needed on macOS.
    @- chflags -R nouchg .git/*
    # Prune tracked refs first because it's a foreground task.
    git remote prune --all
    # Uses 'gc.pruneExpire'.
    git maintenance run --task gc

# NOTE: "Advanced" or "optional" recipe, unlisted but invoked directly.

# Minify the repo by deleting nearly all recreatable files. [CAUTION]
[group('project')]
[private]
minify-repo: clean delete-probable-temp
    uv run pre-commit clean
    uv run pre-commit uninstall
    - rm -f -r .venv
    - rm -f -r .idea
    - rm -f uv.lock

###################################################################################################

# Format *modified* files (via pre-commit).
[group('format')]
format-changes: _format

alias format := format-changes

# Format *all* files (via pre-commit).
[group('format')]
format-all: (_format "--all-files")

# <Internal.>
_format *args:
    - uv run pre-commit run end-of-file-fixer {{ args }}
    - uv run pre-commit run fix-byte-order-marker {{ args }}
    - uv run pre-commit run trailing-whitespace {{ args }}
    - uv run pre-commit run ruff-format {{ args }}
    - uv run pre-commit run prettier {{ args }}

###################################################################################################

# Ruff auto-fix *modified* files (via pre-commit).
[group('fix')]
[no-exit-message]
fix-changes: _stage_precommit (hook "ruff-check")

alias fix := fix-changes

# Ruff auto-fix *all* files (via pre-commit).
[group('fix')]
[no-exit-message]
fix-all: _stage_precommit (hook "ruff-check --all-files")

# Ruff auto-fix *all* files (via ruff directly, passing args).
[group('fix')]
[no-exit-message]
fix-ruff *args: (_fix_ruff args)

# Ruff auto-fix, including unsafe fixes. [CAUTION]
[group('fix')]
[no-exit-message]
[private]
fix-ruff-unsafe *args: (_fix_ruff "--unsafe-fixes" args)

# <Internal.> (FYI: Use `--config` so users can still pass `--output-format`.)
[no-exit-message]
_fix_ruff *args: (ruff "check --fix-only --config 'output-format=\"grouped\"'" args)

# <Internal.>
[no-exit-message]
_stage_precommit:
    git add .pre-commit-config.yaml

###################################################################################################

# `just check-simple check-ruff check-ty check-links`
[group('check')]
[private]
check: check-core check-ruff check-ty check-links

# Check basic rules (via pre-commit).
[group('check')]
check-core:
    # Keep slower hooks lower in the list.
    uv run --no-sync pre-commit run check-filenames
    uv run --no-sync pre-commit run pathvalidate
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

# Check Ruff rules (without auto-fix).
[group('check')]
[no-exit-message]
check-ruff *args: (_check_ruff args)

# Show the number of violations per Ruff rule.
[group('check')]
[no-exit-message]
check-ruff-stats *args: (ruff "check --no-fix --statistics" args)

# Check Ruff Bandit-derived 'S' rules.
[group('check')]
[no-exit-message]
check-bandit *args: (_check_ruff "--select S" args)

# Check Astral's ty typing rules.
[group('check')]
[no-exit-message]
check-ty *args: (run "ty check" args)

# Detect broken hyperlinks (via pre-commit).
[group('check')]
[no-exit-message]
check-links: (hook "markdown-link-check --hook-stage manual --all-files")

# <Internal.> (FYI: Use `--config` so users can still pass `--output-format`.)
[no-exit-message]
_check_ruff *args: (ruff "check --no-fix --config 'output-format=\"grouped\"'" args)

###################################################################################################

# Run tests not marked 'ux'.
[group('test')]
[no-exit-message]
test-non-ux *args: (pytest "-m 'not ux'" args)

alias test := test-non-ux

# Run tests marked 'ux' for manual interaction or verification.
[group('test')]
[no-exit-message]
test-ux *args: (pytest "-m ux" args)

# Run tests not marked 'ux', 'e2e', 'slow', or 'net'.
[group('test')]
[no-exit-message]
test-fast *args: (pytest "-m 'not (ux or e2e or slow or net)'" args)

# Run tests marked 'hypothesis' with Hypothesis's explanation phase.
[group('test')]
[no-exit-message]
test-hypothesis *args: (pytest "-m hypothesis --hypothesis-explain" args)

# Run doctest tests via PyTest.
[group('test')]
[no-exit-message]
test-doctest *args: (pytest "--doctest-modules src/" args)

alias doctest := test-doctest
alias test-doctests := test-doctest

# Run tests not marked 'ux', reporting coverage.
[group('test')]
[no-exit-message]
test-with-cov *args: (pytest "-m 'not ux' --cov" args)

alias test-cov := test-with-cov

# Run PyTest tests, highlighting test durations.
[group('test')]
[no-exit-message]
test-durations *args: (pytest "--durations=0 --durations-min=0" args)

# Run PyTest tests stepwise, starting at last failure.
[group('test')]
[no-exit-message]
[private]
test-stepwise *args: (pytest "--stepwise" args)

# Run PyTest tests, showing minimal output.
[group('test')]
[no-exit-message]
[private]
test-quietly *args: (pytest "--capture=no --tb=line --quiet" args)

# Run PyTest tests, showing tracebacks, locals, and INFO.
[group('test')]
[no-exit-message]
[private]
test-loudly *args: (pytest "--showlocals --full-trace --log-level=INFO --verbose" args)

# Run PyTest tests with pdb debugger.
[group('test')]
[no-exit-message]
[private]
test-with-pdb *args: (pytest "--pdb" args)

###################################################################################################

# Build mkdocs docs from scratch, failing for warnings.
[group('docs')]
[no-exit-message]
build-docs *args: (run "mkdocs build --clean --strict" args)

# Locally serve the mkdocs docs.
[group('docs')]
[no-exit-message]
serve-docs *args: (run "mkdocs serve" args)

###################################################################################################

# `uv run --locked`
[group('alias')]
[no-exit-message]
run +args:
    uv run --locked {{ args }}

# `uv run --locked python`
[group('alias')]
[no-exit-message]
python *args: (run "python" args)

# `uv run --locked pre-commit run {hook}`
[group('alias')]
[no-exit-message]
hook name *args: (run "pre-commit run" name args)

# `uv run --locked ruff`
[group('alias')]
[no-exit-message]
ruff *args: (run "ruff" args)

# `uv run --locked pytest`
[group('alias')]
[no-exit-message]
pytest *args: (run "pytest" args)

# `gh pr create --fill-verbose`
[group('alias')]
[no-exit-message]
pr *args="--web":
    gh pr create --fill-verbose {{ args }}
