# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Command-line interface."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Final

import typer
from loguru import logger
from typer import Argument, Option, Typer, style

from tyranno_sandbox._about import __about__
from tyranno_sandbox._global_vars import EnvGlobalVarsFactory, GlobalVars
from tyranno_sandbox.context import Context, ContextFactory, DefaultContextFactory

ENV: GlobalVars = EnvGlobalVarsFactory()()


@dataclass(slots=True, kw_only=True)
class State:
    """Utility to write messages in typer."""

    context_factory: ContextFactory
    success_color: str
    failure_color: str
    is_dry_run: bool = False
    log_level: int = -1

    def create_context(self) -> Context:
        return self.context_factory(Path.cwd(), ENV, dry_run=self.is_dry_run)

    def set_log_level(self, *, quiet: int, verbose: int) -> None:
        levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "FATAL"]
        self.log_level = levels[max(6, min(0, 3 + quiet - verbose))]
        logger.remove()
        logger.add(sys.stderr, level=self.log_level)

    def show_project_info(self) -> None:
        self.info(f"{__about__['name']} v{__about__['version']}")

    def success(self, msg: str) -> None:
        typer.echo(style(msg, fg=self.success_color, bold=True))

    def failure(self, msg: str) -> None:
        typer.echo(style(msg, fg=self.failure_color, bold=True))

    def info(self, msg: str) -> None:
        typer.echo(msg)


state: Final[State] = State(
    context_factory=DefaultContextFactory(),
    success_color=ENV.success_color,
    failure_color=ENV.failure_color,
)
cli: Final[Typer] = Typer(name="tyranno", no_args_is_help=True)


@cli.callback()
def meta(
    *,
    dry_run: Annotated[bool, Option("--dry-run", help="Just log; don't make any changes")] = False,
    verbose: Annotated[
        int, Option("--verbose", "-v", count=True, help="Log INFO (repeat for DEBUG, TRACE)")
    ] = 0,
    quiet: Annotated[
        int, Option("--quiet", "-q", count=True, help="Hide SUCCESS (repeat for WARNING, ERROR)")
    ] = 0,
) -> None:
    state.set_log_level(quiet=quiet, verbose=verbose)
    state.is_dry_run = dry_run


@cli.command()
def new(
    path: Annotated[Path, Argument(help="name", exists=False, default_factory=Path.cwd)],
    *,
    name: Annotated[str, Option(help="Full project name")] = "my-project",
    license_id: Annotated[str, Option("--license", help="SPDX ID")] = "Apache-2.0",
) -> None:
    state.success(f"Done! Created a new repository under {name}")
    state.success("See https://dmyersturnbull.github.io/tyranno/guide.html")


@cli.command()
def sync() -> None:
    """Syncs project metadata between configured files."""
    state.info("Syncing metadata...")
    # targets = Sync(context).sync()
    # Msg.success(f"Done. Synced to {len(targets)} targets: {targets}")


if __name__ == "__main__":
    cli()
