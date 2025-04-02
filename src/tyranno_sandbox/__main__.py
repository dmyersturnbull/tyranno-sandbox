# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Command-line interface.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from loguru import logger
from typer import Argument, Exit, Option, Typer, colors, echo, style

from tyranno_sandbox._about import __about__
from tyranno_sandbox._global_vars import DefaultGlobalVarsFactory
from tyranno_sandbox.clean import Cleaner
from tyranno_sandbox.context import DefaultContextFactory

_GLOBAL_VARS = DefaultGlobalVarsFactory()()


@dataclass(frozen=True, slots=True, kw_only=True)
class Messenger:
    """"""

    success_color: str = colors.GREEN
    error_color: str = colors.RED

    def success(self, msg: str) -> None:
        echo(style(msg, fg=self.success_color, bold=True))

    def info(self, msg: str) -> None:
        echo(msg)

    def failure(self, msg: str) -> None:
        echo(style(msg, fg=self.error_color, bold=True))

    def show_project_info(self) -> None:
        self.info(f"{__about__.name} v{__about__.version}")


def set_cli_state(verbose: int, quiet: int) -> None:
    levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "FATAL"]
    level = levels[max(6, min(0, 3 + quiet - verbose))]
    logger.remove()
    logger.add(sys.stderr, level=level)


class _Opts:
    dry_run: Annotated[
        bool,
        Option("--dry-run", help="Don't write; just output"),
    ] = False
    verbose: Annotated[
        int,
        Option("--verbose", "-v", count=True, help="Show INFO logging (repeat for DEBUG, then TRACE)"),
    ] = 0
    quiet: Annotated[
        int,
        Option("--quiet", "-q", count=True, help="Hide SUCCESS logging (repeat for WARNING, then ERROR)"),
    ] = 0


messenger = Messenger()
cli = Typer()


class CliCommands:
    """
    Commands for Tyranno.
    """

    @staticmethod
    @cli.command()
    def new(
        path: Annotated[Path, Argument("name", help="name", exists=False)] = Path.cwd(),
        *,
        name: Annotated[str, Option(help="Full project name")] = "my-project",
        license_id: Annotated[str, Option("--license", help="vendor")] = "Apache-2.0",
        dry_run: _Opts.dry_run = False,
        verbose: _Opts.verbose = False,
        quiet: _Opts.quiet = False,
    ) -> None:
        if path is None and name is None:
            raise Exit()
        set_cli_state(verbose=verbose, quiet=quiet)
        context = DefaultContextFactory()(Path(os.getcwd()), dry_run=dry_run)
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
        """
        Sync project metadata between configured files.
        """
        set_cli_state(verbose=verbose, quiet=quiet)
        context = DefaultContextFactory()(Path(os.getcwd()), dry_run=dry_run)
        messenger.info("Syncing metadata...")
        # targets = Sync(context).sync()
        # Msg.success(f"Done. Synced to {len(targets)} targets: {targets}")

    @staticmethod
    @cli.command(help="Removes unwanted files")
    def clean(
        *,
        dry_run: _Opts.dry_run = False,
        verbose: _Opts.verbose = False,
        quiet: _Opts.quiet = False,
    ) -> None:
        set_cli_state(verbose=verbose, quiet=quiet)
        context = DefaultContextFactory()(Path(os.getcwd()), dry_run=dry_run)
        trashed = list(Cleaner(context).run())
        messenger.info(f"Trashed {len(trashed)} paths.")


if __name__ == "__main__":
    cli()
