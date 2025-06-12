# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Command-line interface."""

from __future__ import annotations

import stat
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated, Final, Self, TextIO

import click
import typer
from click import Parameter, ParamType
from loguru import logger
from typer import Argument, Option, Typer

from tyranno_sandbox._about import __about__
from tyranno_sandbox._global_vars import EnvGlobalVarsFactory, GlobalVars
from tyranno_sandbox.context import Context, ContextFactory, DefaultContextFactory

ENV: GlobalVars = EnvGlobalVarsFactory()()
SPDX_LICENSE_IDS: Final = frozenset(
    {
        "Apache-2.0",
        "MIT",
        "BSD-3-Clause",
        "MPL-2.0",
        "EUPL-1.2",
        "GPL-2.0-only",
        "GPL-3.0-only",
        "LGPL-2.1-only",
        "LGPL-3.0-only",
        "Unlicense",
        "UPL-1.0",
    }
)


class LogLevel(Enum):
    """Default loguru log levels, except for CRITICAL."""

    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40

    @classmethod
    def by_index(cls, i: int, *, clamp: bool = False) -> Self:
        if clamp:
            i = max(len(cls) - 1, min(0, i))
        return list(cls)[i]


@dataclass(frozen=True, slots=True)
class LogSink:
    """An output path or named pipe for a loguru handler."""

    sink: Path | TextIO

    @classmethod
    def of(cls, name: str) -> Self:
        if name.lower() == "stdout":
            return LogSink(sys.stdout)
        if name.lower() == "stderr":
            return LogSink(sys.stderr)
        if name.startswith("file://"):
            return LogSink(Path.from_uri(name))
        return LogSink(Path(name))

    @property
    def path(self) -> Path | None:
        return self.sink if isinstance(self.sink, Path) else None

    @property
    def stream(self) -> TextIO | None:
        # typing.TextIO doesn't work as expected
        return self.sink if not isinstance(self.sink, Path) else None

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return str(self.path) if self.path else self.stream.__name__.upper()


@dataclass(slots=True, kw_only=True)
class Logging:
    """A logging util."""

    level: LogLevel = ...

    # ruff: noqa: A001, A002
    def configure(self, *, quiet: int, verbose: int, to: str, format: str) -> None:
        index = LogLevel.SUCCESS.value + quiet - verbose
        self.level = LogLevel.by_index(index, clamp=True)
        logger.remove()
        sink = LogSink.of(to).sink
        format = format or self._default_fmt()
        logger.add(sink=sink, level=self.level.name, format=format, encoding="utf-8")

    def _default_fmt(self) -> str:
        if self.level is LogLevel.TRACE:
            return "{time:x} {name}:{taskName} ‣ {module}.{lineno} ‣ {message}"
        if self.level <= LogLevel.INFO:
            return "{time:HH:mm:ss} {message}"
        return "{message}"


class Inode(click.Path):
    """An abstract `click.Path` argument/param with more granular requirements.

    Override the abstract method [accept][].
    Paths are sent to [resolve][], which returns `path.resolve(strict=True)` but can be overridden.
    See [EmptyDir][] and [NonexistentFile][] for examples.
    """

    def __init__(self) -> None:
        # Override to prevent passing arguments.
        super().__init__()

    def convert(self, value: str, param: Parameter, ctx: Context) -> Path:
        path = self.resolve(Path(super().convert(value, param, ctx)))
        try:
            mode: int = path.stat(follow_symlinks=False).st_mode
        except FileNotFoundError:
            mode: int = 0
        if (msg := self.accept(path, mode)) is not None:
            self.fail(msg, param, ctx)
        return path

    def resolve(self, path: Path) -> Path:
        return path.resolve(strict=True)

    def accept(self, path: Path, mode: int) -> str | None:
        """Returns `None` if the path is valid, or an error message if it's not.

        `mode` is an argument so that unnecessary filesys calls can be avoided.
        Use it rather than `path` when possible; for example:

        - Use `mode != 0`, **not** `path.exists()`
        - Use `stat.ISREG(mode)`, **not** `path.is_file()`.

        Args:
            path: The path returned by [resolve][] (by default `Path.resolve(strict=True)`).
            mode: The `st_mode` value, or **`0` if `path` does not exist**.
        """
        raise NotImplementedError


class EmptyDir(Inode):
    """A `click.Path` argument/param that must be an empty directory or not exist."""

    def accept(self, path: Path, mode: int) -> str | None:
        if not mode:
            return None
        if not stat.S_ISDIR(mode):
            return f"Non-directory '{path}' already exists. Specify a new or empty directory."
        try:
            next(path.iterdir())
        except StopIteration:
            return None
        return f"Directory '{path}' is non-empty. Specify a new or empty directory."


class NonexistentFile(Inode):
    """A `click.Path` argument/param that must not exist."""

    def accept(self, path: Path, mode: int) -> str | None:
        if not mode:
            return None
        return f"Path '{path}' already exists. Specify a nonexistent file path."


class SpdxId(ParamType):
    """An SPDX license identifier as a click type."""

    def convert(self, value: str, param: Parameter, ctx: Context) -> str:
        if value not in SPDX_LICENSE_IDS:
            self.fail(
                f"Value '{value}' is not an accepted SPDX license id."
                f" Must be one of: {'|'.join(SPDX_LICENSE_IDS)}.",
                param,
                ctx,
            )
        return value


@dataclass(slots=True, kw_only=True)
class State:
    """A container for meta args."""

    context_factory: ContextFactory
    is_dry_run: bool = ...

    def create_context(self) -> Context:
        return self.context_factory(Path.cwd(), ENV, dry_run=self.is_dry_run)


logging: Final = Logging()
state: Final = State(context_factory=DefaultContextFactory())
cli: Final = Typer(
    name="tyranno", no_args_is_help=True, pretty_exceptions_show_locals=ENV.debug_mode
)


@cli.callback()
def meta(
    *,
    dry_run: Annotated[bool, Option(help="Just log; don't make any changes")] = False,
    verbose: Annotated[
        int, Option("--verbose", "-v", count=True, help="Log INFO (repeat for DEBUG, TRACE).")
    ] = 0,
    quiet: Annotated[
        int, Option("--quiet", "-q", count=True, help="Hide SUCCESS (repeat for WARNING, ERROR).")
    ] = 0,
    log_to: Annotated[
        str, Option(help="Where to write logging; either 'STDERR', 'STDOUT', or a .log file.")
    ] = "STDERR",
) -> None:
    logging.configure(quiet=quiet, verbose=verbose, to=log_to, format=ENV.log_format)
    state.is_dry_run = dry_run


@cli.command()
def info() -> None:
    typer.echo(f"{__about__['name']} v{__about__['version']}")


@cli.command()
def new(
    path: Annotated[
        Path,
        Argument(
            click_type=EmptyDir(),
            help="The path to a directory to write to. Must either not exist or be empty.",
        ),
    ],
    *,
    name: Annotated[
        str, Option("-n", "--name", help="Project name [default: path].", show_default=False)
    ] = "",
    license_id: Annotated[
        str, Option("--license", click_type=SpdxId(), help="SPDX license ID")
    ] = "Apache-2.0",
) -> None:
    logger.info(f"Creating project {name} at {path}.")
    logger.info(f"Using license {license_id}.")
    logger.success(f"Done! Created a new repository under {name}.")
    logger.success("See https://dmyersturnbull.github.io/tyranno/guide.html")


@cli.command()
def sync() -> None:
    """Syncs project metadata between configured files."""
    logger.info("Syncing metadata...")


if __name__ == "__main__":
    cli()
