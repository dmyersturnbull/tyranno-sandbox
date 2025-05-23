# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Command-line interface."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Final

from loguru import logger
from typer import Argument, Option, Typer, echo, style

from tyranno_sandbox._about import __about__
from tyranno_sandbox._global_vars import EnvGlobalVarsFactory, GlobalVars
from tyranno_sandbox.context import ContextFactory, DefaultContextFactory

try:
    # noinspection PyUnresolvedReferences
    from rich.console import Console

    console = Console(stderr=sys.stdout.isatty())
except ImportError:
    console = None

_ENV: GlobalVars = EnvGlobalVarsFactory()()


@dataclass(frozen=True, slots=True, kw_only=True)
class Messenger:
    """Utility to write messages in typer."""

    success_color: str
    failure_color: str

    def success(self, msg: str) -> None:
        echo(style(msg, fg=self.success_color, bold=True))

    def info(self, msg: str) -> None:
        echo(msg)

    def failure(self, msg: str) -> None:
        echo(style(msg, fg=self.failure_color, bold=True))

    def show_project_info(self) -> None:
        self.info(f"{__about__['name']} v{__about__['version']}")


def set_cli_state(verbose: int, quiet: int) -> None:
    levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "FATAL"]
    level = levels[max(6, min(0, 3 + quiet - verbose))]
    logger.remove()
    logger.add(sys.stderr, level=level)


class _Opts:
    dry_run: Annotated[bool, Option("--dry-run", help="Just log; don't make any changes")] = False
    verbose: Annotated[
        int, Option("--verbose", "-v", count=True, help="Log INFO (repeat for DEBUG, TRACE)")
    ] = 0
    quiet: Annotated[
        int, Option("--quiet", "-q", count=True, help="Hide SUCCESS (repeat for WARNING, ERROR)")
    ] = 0


messenger: Final[Messenger] = Messenger(
    success_color=_ENV.success_color, failure_color=_ENV.failure_color
)
cli: Final[Typer] = Typer(name="tyranno")
context_factory: Final[ContextFactory] = DefaultContextFactory()


class CliCommands:
    """Commands for Tyranno."""

    @staticmethod
    @cli.command()
    def new(
        path: Annotated[Path, Argument(help="name", exists=False, default_factory=Path.cwd)],
        *,
        name: Annotated[str, Option(help="Full project name")] = "my-project",
        license_id: Annotated[str, Option("--license", help="SPDX ID")] = "Apache-2.0",
        dry_run: _Opts.dry_run = False,
        verbose: _Opts.verbose = False,
        quiet: _Opts.quiet = False,
    ) -> None:
        set_cli_state(verbose=verbose, quiet=quiet)
        context = context_factory(Path.cwd(), _ENV, dry_run=dry_run)
        messenger.info(f"Done! Created a new repository under {name}")
        messenger.success("See https://dmyersturnbull.github.io/tyranno/guide.html")

    @staticmethod
    @cli.command()
    def sync(
        *,
        dry_run: _Opts.dry_run = False,
        verbose: _Opts.verbose = False,
        quiet: _Opts.quiet = False,
    ) -> None:
        """Syncs project metadata between configured files."""
        set_cli_state(verbose=verbose, quiet=quiet)
        context = context_factory(Path.cwd(), _ENV, dry_run=dry_run)
        messenger.info("Syncing metadata...")
        # targets = Sync(context).sync()
        # Msg.success(f"Done. Synced to {len(targets)} targets: {targets}")


if __name__ == "__main__":
    cli()
