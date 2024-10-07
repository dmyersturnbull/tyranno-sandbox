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

## Local setup

_(After following the
[contributing guide](https://dmyersturnbull.github.io/ref/contributor-guide/))_
You will need to have
[NPM](https://docs.npmjs.com/cli/v10/commands/npm-install)
and
[Hatch](https://hatch.pypa.io/latest/install/)
installed.

<small>
<b>Windows users:</b>
This repo uses the Linux and macOS `\n` for newlines, never `\r\n`.
Setting `git config core.autocrlf input` will let you use `\r\n` locally
but convert them to `\n` on commit.
</small>

### Scripts

The `pyproject.toml` defines some Hatch scripts, including

- `hatch run format-python` to format and auto-fix using Ruff
- `hatch run format` to also run Prettier
- `hatch run check` to find lint violations using Ruff
- `hatch run test` to run tests (excludes markers `slow`, `net`, and `ux`)
- `hatch run test -m 'not ux'` to run all non-interactive tests
- `hatch run serve-docs` to build and show the docs

### Configuring linting and formatting

This will configure formatters and some checks that run every commit.
This step is optional but encouraged.

In your local clone, run these commands:

1. `pip install pre-commit`
2. `pre-commit install`
3. `npm install .`
