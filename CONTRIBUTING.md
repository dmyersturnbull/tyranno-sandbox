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

## Local tools

The [`justfile`](justfile) lists useful commands for development.
Consider
[installing just](https://github.com/casey/just?tab=readme-ov-file#packages)
so you can run (e.g.) `just format`.
On Windows, you may need
[Git for Windows](https://gitforwindows.org/),
[posh-git](https://github.com/dahlbyk/posh-git),
or similar.

> [!TIP]
> Consider setting `git config --global diff.algorithm histogram` for nicer diffs.

## PR comment commands

You can trigger some workflows via PR comments.
Each command can be anywhere in a comment but must be on its own line.
Commands start with `/plz`.

Some commands can run on either the HEAD commit or the MERGE commit.
As a rule of thumb, linters default to HEAD,
whereas tests (including smoke tests like building images) default to MERGE.

- `[ref]` means `head` or `merge` (e.g. `/plz test head`).
- Parenthesized values in _runs on_ are defaults.
- 🧪 means experimental.
- `[]` encloses optional arguments.

| Command                          | Runs on   | Action                                        |
|----------------------------------|-----------|-----------------------------------------------|
| `/plz format`                    | HEAD      | Formats all files w/ `style:` commit.         |
| 🧪 `/plz label`                  | HEAD      | Apply proper labels to PR.                    |
| `/plz update`                    | HEAD      | Bumps lock file versions w/ `build:` commit.  |
| `/plz lint [types] [ref]`        | _(HEAD)_  | Finds issues in modified files.               |
| 🧪 `/plz lint all [types] [ref]` | _(HEAD)_  | Finds issues in all files.                    |
| `/plz audit [ref]`               | _(HEAD)_  | Finds security issues in modified files.      |
| `/plz audit all [ref]`           | _(HEAD)_  | Finds security issues in all files.           |
| `/plz check image [ref]`         | _(MERGE)_ | Verifies Docker builds on Ubuntu and Windows. |
| `/plz check docs [ref]`          | _(MERGE)_ | Verifies that docs build.                     |
| `/plz quick test [ref]`          | _(MERGE)_ | Runs PyTest tests with no markers.            |
| `/plz test [ref]`                | _(MERGE)_ | Runs PyTest tests not marked `ux` or `e2e`.   |
| 🧪 `/plz e2e test [ref]`         | _(MERGE)_ | Runs end-to-end tests via Docker Compose.     |
