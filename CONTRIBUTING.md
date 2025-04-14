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

## Tools

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
