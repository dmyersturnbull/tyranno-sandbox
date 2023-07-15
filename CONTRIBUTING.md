# Contributing

# CICD <!--<< :tyranno: ${.name~.title(@)~} -->

<!-- :tyranno: [${.license.name}](${.license.url}) -->
Licensed under the [Apache License, version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
New issues and pull requests are welcome.
Contributors are asked to abide by both the
[GitHub community guidelines](https://docs.github.com/en/site-policy/github-terms/github-community-guidelines)
and the [Contributor Code of Conduct, version 2.0](https://www.contributor-covenant.org/version/2/0/code_of_conduct/).

### Commit messages

Follows [Semantic Versioning 2](https://semver.org/spec/v2.0.0.html)
and [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
Commit types mapped to pull request labels and release notes sections by the following table:


| Commit keyword   | Section              | semver   | issue label(s)        | note   |
|------------------|----------------------|----------|-----------------------|--------|
| `!`              | `⚠ BREAKING CHANGES` | major    | `breaking`            | 1      |
| `feat:`          | `🎁 Features`        | minor    | `type: feature`       |        |
| `fix:`           | `🐛 Bug fixes`       | patch    | `type: fix`           |        |
| `security`       | `🔒 Security`        | N/A      | `security`            |        |
| `build:`         | `🔧 Build System`    | patch    | `type: build`         |        |
| `perf:`          | `🚀 Performance`     | patch    | `type: performance`   |        |
| `docs:`          | `📝 Documentation`   | patch    | `type: docs`          |        |
| `test:`          | `🚨 Tests`           | N/A      | `type: test`          |        |
| `ci:`            | `🧹 Miscellaneous`   | N/A      | `type: misc`          |        |
| `refactor:`      | `🧹 Miscellaneous`   | N/A      | `type: misc`          |        |
| `style:`         | `🧹 Miscellaneous`   | N/A      | `type: misc`          |        |
| `chore:`         | `🧹 Miscellaneous`   | N/A      | `type: misc`          |        |
| `revert:`        | N/A                  | N/A      | N/A                   | 2      |
| none             | N/A                  | N/A      | `exclude`             | 3      |

**Notes:**
1. `!` suffix, or `BREAKING:` prefix in the body.
2. Only apply when reverting commits in the same feature branch, and state the reverted commit
   in the header. Both commits will then be squashed before merging.
   If made in separate feature branches, then specific types like `fix:` must be used instead.
3. Apply `exclude` to hide changes like typo corrections from GitHub Release notes.


### Pull requests

Please add your name to the contributors in `pyproject.toml`.
Feel free to make a draft pull request and solicit feedback from the maintainers.

### Publishing a new version

1. Bump the version in `tool.poetry.version` in `pyproject.toml`, following the rules described below.
2. Create a [new release](https://github.com/dmyersturnbull/tyranno/releases/new)
   with both the name and tag set to something like `v1.4.13` (keep the _v_).
3. An hour later, check that the _publish on release creation_
   [workflow](https://github.com/dmyersturnbull/tyranno/actions) passes
   and that the PyPi, Docker Hub, and GitHub Package versions are updated as shown in the
   shields on the readme.
4. Check for a pull request from regro-cf-autotick-bot on the
   [feedstock](https://github.com/conda-forge/tyranno-feedstock).
   _If you have not changed the dependencies or version ranges_, go ahead and merge it.
   Otherwise, [update the recipe](https://github.com/conda-forge/tyranno-feedstock/blob/main/recipe/meta.yaml)
   with those changes under `run:`, also updating `{% set version` and `sha256` with the
   changes from regro-cf-autotick-bot. You can alternatively re-run `tyranno recipe`
   to generate a new recipe and copy it to the feedstock.
5. Twenty minutes later, verify that the Conda-Forge shield is updated.

#### Versioning

Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Git tags and GitHub releases are with `v` (e.g. `v0.1.1`).

For each `major "." minor "." patch`, we require a progression from early builds to final release.
Steps may be skipped but may not occur out of order (e.g., no alpha after a beta).
If `major > 0`, at least one alpha, beta, or RC should be made first.
1. Early builds: `"v" major "." minor "." patch "-" [0-9]+ ("+" platform)?`
2. Alpha releases: `"v" major "." minor "." patch "-alpha" [1-9][0-9]* ("+" platform)?`
3. Beta releases: `"v" major "." minor "." patch "-beta" [1-9][0-9]* ("+" platform)?`
4. Release candidates: `"v" major "." minor "." patch "-rc" [1-9][0-9]* ("+" platform)?`
5. Final releases: `"v" major "." minor "." patch "-rc" [1-9][0-9]* ("+" platform)?`
