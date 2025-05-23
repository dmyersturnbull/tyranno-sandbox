# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Utilities for tests."""

import contextlib
import io
import logging
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from os import PathLike
from pathlib import Path
from types import TracebackType
from typing import Self, override

__all__ = ["TestHelper", "logger"]

from zoneinfo import ZoneInfo

# Separate logging in the main package vs. inside test functions
logger = logging.getLogger(Path(__file__).parent.parent.name + "::test")


class Capture(contextlib.ExitStack):
    def __init__(self) -> None:
        super().__init__()
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()

    @property
    def stdout(self) -> str:
        return self._stdout.getvalue()

    @property
    def stderr(self) -> str:
        return self._stderr.getvalue()

    @override
    def __enter__(self) -> Self:
        logger.debug("Capturing stdout and stderr")
        super().__enter__()
        self._stdout_context = self.enter_context(contextlib.redirect_stdout(self._stdout))
        # If the next line failed, the stdout context wouldn't exit
        # But this line is very unlikely to fail in practice
        self._stderr_context = self.enter_context(contextlib.redirect_stderr(self._stderr))
        return self

    @override
    def __exit__(
        self, exc_type: type[BaseException], exc_value: BaseException, traceback: TracebackType
    ) -> None:
        logger.debug("Finished capturing stdout and stderr")
        # The ExitStack handles everything
        super().__exit__(exc_type, exc_value, traceback)


@dataclass(frozen=True, slots=True)
class TestHelper:
    """A set of utilities for tests classes.
    Use [resource][] to get a file under `tests/resources/`.
    """

    _start_dt: datetime = field(default_factory=lambda: datetime.now().astimezone(), init=False)
    _start_s: float = field(default_factory=time.monotonic, init=False)

    @classmethod
    @contextlib.contextmanager
    def capture(cls) -> Generator[Capture]:
        """Context manager that captures stdout and stderr in a `Capture` object that contains both.
        Useful for testing code that prints to stdout and/or stderr.

        Yields:
            A [Capture][] instance, which contains `.stdout` and `.stderr`
        """
        with Capture() as cap:
            yield cap

    @classmethod
    def resource(cls, *nodes: PathLike | str) -> Path:
        """Gets a path of a test resource file under `resources/`.

        Arguments:
            nodes: Path nodes under the `resources/` dir

        Returns:
            The Path `resources`/`<node-1>`/`<node-2>`/.../`<node-n>`
        """
        return Path(__package__, "resources", *nodes).resolve()

    @property
    def start_datetime(self) -> datetime:
        return self._start_dt

    @property
    def start_timestamp_safe_local(self) -> str:
        return self._start_dt.strftime("%Y-%m-%d %H-%M-%S.%f%z")

    @property
    def start_timestamp_safe_utc(self) -> str:
        return self._start_dt.astimezone(ZoneInfo("Etc/UTC")).strftime("%Y-%m-%d %H-%M-%S.%fZ")

    @property
    def time_elapsed(self) -> timedelta:
        return timedelta(seconds=time.monotonic() - self._start_s)
