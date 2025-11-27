<!--
Render a jagged grid of badges.
Use line breaks to separate rows, not paragraphs; the latter looks ugly.
In GitHub-flavored Markdown, do this by ending the line with `\` .
-->
<!-- ::tyranno:: [![Version status](https://img.shields.io/pypi/status/$<<project.name>>?label=Status)](https://pypi.org/project/$<<project.name>>)-->
<!-- ::tyranno:: [![Version on PyPi](https://badgen.net/pypi/v/$<<project.name>>?label=PyPi)-->
<!-- ::tyranno:: [![Version on GitHub](https://badgen.net/github/release/$<<.frag>>/stable?label=GitHub)]($<<.frag>>/releases)-->
<!-- ::tyranno:: [![Version on Docker Hub](https://img.shields.io/docker/v/$<<.frag>>?color=green&label=Docker%20Hub)](https://hub.docker.com/repository/docker/$<<.frag>>)\-->
<!-- ::tyranno:: [![Build (Actions)](https://img.shields.io/github/workflow/status/$<<.frag>>/test?label=Tests)]($<<.frag>>/actions)-->
<!-- ::tyranno:: [![Coverage (coveralls)](https://badgen.net/coveralls/c/github/$<<project.name>>/$<<project.name>>?label=Coveralls)](https://coveralls.io/github/$<<.frag>>?branch=main)-->
<!-- ::tyranno:: [![Coverage (codecov)](https://badgen.net/codecov/c/github/$<<.frag>>?label=CodeCov)](https://codecov.io/gh/$<<.frag>>)\-->
<!-- ::tyranno:: [![Maintainability (Code Climate)](https://badgen.net/codeclimate/maintainability/$<<.frag>>)](https://codeclimate.com/github/$<<.frag>>/maintainability)-->
<!-- ::tyranno:: [![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/$<<.frag>>/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/$<<.frag>>/?branch=main)-->
<!-- ::tyranno:: [![CodeFactor](https://www.codefactor.io/repository/github/$<<.frag>>/badge)](https://www.codefactor.io/repository/github/$<<.frag>>)\-->
<!-- ::tyranno:: [![License](https://badgen.net/pypi/license/$<<project.name>>?label=License)]($<<project.license.url>>)-->
<!-- ::tyranno:: [![DOI](https://zenodo.org/badge/DOI/$<<.doi>>.svg)](https://doi.org/$<<.doi>>)-->
<!-- ::tyranno:: [![Created with Tyrannosaurus](https://img.shields.io/badge/Created_with-tyranno-sandbox-0000ff.svg)](https://github.com/$<<.frag>>)-->

[![Version status](https://img.shields.io/pypi/status/tyranno-sandbox?label=Status)](https://pypi.org/project/tyranno-sandbox)
[![Version on PyPi](https://badgen.net/pypi/v/tyranno-sandbox?label=PyPi)](https://pypi.org/project/tyranno-sandbox)
[![Version on GitHub](https://badgen.net/github/release/dmyersturnbull/tyranno-sandbox/stable?label=GitHub)](https://github.com/dmyersturnbull/tyranno-sandbox/releases)
[![Version on Docker Hub](https://img.shields.io/docker/v/dmyersturnbull/tyranno-sandbox?color=green&label=Docker%20Hub)](https://hub.docker.com/repository/docker/dmyersturnbull/tyranno-sandbox)
[![Build (Actions)](https://img.shields.io/github/actions/workflow/status/dmyersturnbull/tyranno-sandbox/push-main.yml?label=Tests)](https://github.com/dmyersturnbull/tyranno-sandbox/actions)
[![Coverage (coveralls)](https://badgen.net/coveralls/c/github/dmyersturnbull/tyranno-sandbox?label=Coveralls)](https://coveralls.io/github/dmyersturnbull/tyranno-sandbox?branch=main)
[![Coverage (codecov)](https://badgen.net/codecov/c/github/dmyersturnbull/tyranno-sandbox?label=CodeCov)](https://codecov.io/gh/dmyersturnbull/tyranno-sandbox)\
[![Maintainability (Code Climate)](https://badgen.net/codeclimate/maintainability/dmyersturnbull/tyranno-sandbox)](https://codeclimate.com/github/dmyersturnbull/tyranno-sandbox/maintainability)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/dmyersturnbull/tyranno-sandbox/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/dmyersturnbull/tyranno-sandbox/?branch=main)
[![CodeFactor](https://www.codefactor.io/repository/github/dmyersturnbull/tyranno-sandbox/badge)](https://www.codefactor.io/repository/github/dmyersturnbull/tyranno-sandbox)\
[![License](https://badgen.net/pypi/license/tyranno-sandbox?label=License)](https://opensource.org/licenses/Apache-2.0)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4485186.svg)](https://doi.org/10.5281/zenodo.4485186)
[![Created with Tyrannosaurus](https://img.shields.io/badge/Created_with-Tyrannosaurus-0000ff.svg)](https://github.com/dmyersturnbull/tyranno-sandbox)

# Sandbox for Tyrannosaurus

This is the prototype next-gen [tyranno-sandbox](https://github.com/dmyersturnbull/tyranno-sandbox).
When ready, that repository will be updated.

---

Tyranno is both:

1. _As a template repository:_
   A very modern Python project template using
   [uv](https://docs.astral.sh/uv/),
   [Ruff](https://github.com/astral-sh/ruff),
   [Biome](https://biomejs.dev/),
   [GitHub actions](https://docs.github.com/en/actions), and
   [Zensical](https://zensical.org/).
2. _As an installable tool:_
   A small but capable polyglot metaprogramming tool
   intended for keeping project metadata updated according to special comments.

## This template repository

### 🎁 Features

Extensive autoformatting, advanced linting, release notes generation,
automated publishing to PyPi + container registries + GH Releases + GH Pages,
reports to [Coveralls](https://coveralls.io/) or [Codecov](https://codecov.io/),
and [more](https://github.com/dmyersturnbull/tyranno-sandbox/blob/main/.github/workflows).

It’s opinionated but completely flexible.

**Everything is optional.**
Not using Docker? Delete the Dockerfile.
Hate the GitHub workflows? Delete them.

**There’s no magic anywhere.**
Uses only standard tools in transparent ways.

**It’s carefully designed.**
You don’t need to do the research, prototyping, and testing to find
the best tools and ensure they coexist peacefully.
Over 100 hours went into what’s here.

### ✏️ How to start

> [!TIP]
> :**Making a repo supporting a scientific publication?**
> Tyrannosaurus has a little sister,
> [science-notebook-template 🧪](https://github.com/dmyersturnbull/science-notebook-template).

First, [install uv](https://docs.astral.sh/uv/getting-started/installation/).
I also recommend installing [just](https://github.com/casey/just) (`uv tool install just`)
and the [GitHub CLI](https://cli.github.com/)
_([installation](https://github.com/cli/cli#installation))_.

Create projects however you normally do.
Or:

1. Clone this repo.
2. Edit `pyproject.toml` as needed, especially `[project]` and `[tool.tyranno.data]`.
3. Add or remove any files as you see fit.
   For example, if you don’t use Docker, delete `Dockerfile`.
4. Add your code to `src/` and `tests/`.
5. Run `just init`.

I recommend a PR-only workflow.
This enables
**good** autogenerated release notes using
[GitHub’s feature](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes),
[Release Drafter](https://github.com/release-drafter/release-drafter)
or something else.

## Tyranno the installable tool

`tyranno` is also an installable tool.
It is currently tailored to Python-primary projects,
but it works with any language that supports comments.
To use it, list `tyranno` in your dev dependencies (`dependency-groups`).

The CLI is invoked as `tyranno`:

- `tyranno sync` (_covered below_)
- `tyranno reqs` to bump dependencies
- `tyranno req <pkg>` to pull info about _pkg_
- `tyranno new` to generate new projects interactively
- `tyranno help [<cmd>]` for usage

### Syncing

`tyranno sync` finds specially formatted comments in target globs (`tool.tyranno.targets`).
For example, assuming you’ve listed `README.md` as a target:

```markdown
<!-- ::tyranno:: $<<project.description>> -->

This next line is the string from pyproject.toml.

<!-- ::tyranno:: By $<<$.project.authors[*].name|sort(@)|join(', ', @>> -->

By Kerri Johnson, Henry Chen
```

You can use
[JSONPath](https://datatracker.ietf.org/doc/html/rfc9535)
(provided by [python-jsonpath](https://github.com/jg-rp/python-jsonpath))
expressions as seen above.

Multiple lines can also be replaced; see below for details.

### The first path element

Every JSONPath expression is assumed to already be inside `tool.tyranno.data`.
That means that the first path element is significant:

- `.key` (or equivalently `@.key`) gets `tool.tyranno.data.key`.
  _E.g.: `$<<project.name>>`._
- `$.key` accesses the `pyproject.toml` root.
  _E.g.: `$<<$.project.name>>`._
- `^@.key` only works inside a YAML, TOML, JSONC, XML, or HTML file.
  It gets `key` under the current key inside the file being processed.
  For XML and HTML, attributes are ignored and cannot be accessed.
  _E.g.: `$<<^@.versions>>`._
- Similarly, `^$.key` gets `key` under the root of the file being processed.
  _E.g. `$<<^.site_name>>` inside `zensical.toml`._

### A more complex example

Maybe you want your GitHub workflows to use your `pyproject.toml` Python version.
Define `default-python` in `[tool.tyranno.data]`
and reference it in a JMESPath expression using a tyranno-defined `pep440_` function.

```yaml
- uses: astral-sh/setup-uv@v7
  with:
    # ::tyranno:: python-version: "$<< .'default-python' | pep440_minor(@) >>"
    python-version: "3.14"
```

### Complex single-line expressions

If wanted, you could define `default-python-version` dynamically as well,
along with a list of Python versions to test in CI:

```toml
# Get the highest patch version for each compatible Python minor version.
# ::tyranno:: ci-python = $<<
# project.requires-python
# | pep440_spec_of('python', @)
# | pep440_find_matches(@)
# | pep440_max_per(@, 'minor')
# >>
test-python-versions = ["3.11.11", "3.12.8", "3.13.2", "3.14.0"]
# Use the highest version for main CI/CD tasks.
# ::tyranno:: default-python-version = "$<< .'test-python-versions' | pep440_max(@) >>"
default-python = "3.14.0"
```

### Multi-line expressions

There are two ways to fill multiple lines:

- consecutive `::tyranno::` lines
- output surrounded by `::tyranno start::` and `::tyranno end::` (_blocks_)

#### Option A: consecutive `::tyranno::` lines

```java
// ::tyranno:: public final String NOTICE = "$<<project.name>>"
// ::tyranno::     + " version " + "$<<project.version>>";
public final String NOTICE = project.name
    + " version " + project.version;
```

#### Option B: block syntax

```java
// ::tyranno start::
// ::tyranno:: List<String> command = List.of($<<.command|yaml_multiline(@, 4, true)>>);
List<String> command = List.of(
    "#!/usr/bin/env bash",
    "printf 'Hello, world!\\n'",
    "exit 0"
);
// ::tyranno end::
```

`::tyranno start::` and `::tyranno end::` are needed whenever the number of lines can vary.
Tyrannosaurus otherwise doesn't know how many existing lines it needs to replace.

### Aliases

In `pyproject.toml` (or a file listed in `tool.tyranno.sources`), you can use
`::tyranno alias:: key = value` as shorthand for `::tyranno:: key = $<< value >>`.
This can avoid storing a generated temporary value inside `pyproject.toml`.
For example, you might use `::tyranno alias:: readme = $<<contents('readme.md')>>`.

## 🍁 Contributing

New issues and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/tyranno-sandbox/blob/master/CONTRIBUTING.md)
and [security policy](https://github.com/dmyersturnbull/tyranno-sandbox/blob/main/SECURITY.md).

```text
                    __
                   / _)
        _.----._/ /  _ ,
  .___/        / / = = ,
:----- | ) - ( |
       : :   : :
```

<small>It’s a <s>turtle with arms.</s> <s>dog.</s> <s>misshapen mango?</s> T. rex.</small>
