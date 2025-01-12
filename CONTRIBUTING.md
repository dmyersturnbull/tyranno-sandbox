# Contributing

Contributions are always welcome.
Before writing any code, please **open an issue** to discuss the intended change.
Please only address one issue per PR, and
[link the PR to the issue](https://docs.github.com/en/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue).
For example, write `Fixes #123` in the PR description.

Feel free to open a PR well before it’s complete.
Just mark it as a draft until it’s ready for review.

Refer to the
[contributing guide](https://dmyersturnbull.github.io/ref/contributor-guide/)
for more details.

Maintainers should instead refer to the
[maintainer guide](https://dmyersturnbull.github.io/ref/maintainer-guide/).

## Reference of common command

### Clean and format

- **Clean**
  Removes unnecessary files. Safe to run anytime.
  **Command:** `uvx tyranno clean`
- **Auto-fix Python**
  Formats and fixes code issues with Ruff. Does not error.
  **Command:** `uvx ruff format && uvx ruff check --fix-only`
- **Auto-format all files**
  Runs pre-commit hooks on all files, using Ruff and Prettier.
  Formats and auto-fixes files, and will error if changes are made.
  **Command:** `uvx pre-commit run --all-files`

#### Linting

### General

- `uvx pre-commit install`
  to initialize pre-commit _(make sure to run this)_.
- `uv sync`
  to sync your venv to the `pyproject.toml`.
- `uv lock --upgrade`
  to bump dependency versions in the lock file.

#### Formatting

These are run automatically on commit.

- `uvx pre-commit run prettier`
  to run [Prettier](https://prettier.io/).
- `uvx ruff format`
  (equivalently, `uvx pre-commit run ruff-format`)
  to format code and docs using the
  [Ruff formatter](https://docs.astral.sh/ruff/formatter/).
- `uvx ruff check . --fix-only`
  (equivalently, `uvx pre-commit run ruff`)
  to auto-fix problems using the
  [Ruff linter](https://docs.astral.sh/ruff/linter/).

### Linting

You should run these manually.

- `uvx ruff check . --no-fix`
  to show potential problems.
- `uvx ruff check --no-fix --select S .`
  to show only potential security problems.
- `uvx mypy --non-interactive src tests`
  to check typing using
  [MyPy](https://mypy-lang.org/).

### Testing

- `uvx pytest`
  to run unit tests.
- `uvx pytest -m (slow or net or ux)`
  to run tests that are integration, slow, network-dependent, or interactive.

### Checking docs

- `uvx mkdocs serve [args]`
  to build serve docs locally.
- `uvx mkdocs build --clean --strict`
  to build docs, failing on any warning.

### Deploying docs (for maintainers)

> [!WARNING] These commands can modify the live docs on GitHub Pages.

- `uvx mike deploy latest --update-aliases`
  to deploy the latest version, updating the `latest` alias.
- `uvx mike delete --all`
  to delete all versions
- `uvx mike deploy --strict`
  to redeploy all versions.
  Use if prior deployments failed, or after deleting versions.
- `uvx mike serve --strict`
  Serves all versions of the documentation locally, including a version selector.
