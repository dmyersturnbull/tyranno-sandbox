# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""
Utilities for tests.
"""

import contextlib
import io
import logging
import time
from datetime import datetime
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Self
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from types import TracebackType

__all__ = ["TestHelper"]

# Separate logging in the main package vs. inside test functions
logger_name = Path(__file__).parent.parent.name.upper() + ".TEST"
_logger = logging.getLogger(logger_name)


class Capture(contextlib.ExitStack):
    def __init__(self: Self) -> None:
        super().__init__()
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()

    @property
    def stdout(self: Self) -> str:
        return self._stdout.getvalue()

    @property
    def stderr(self: Self) -> str:
        return self._stderr.getvalue()

    def __enter__(self: Self) -> Self:
        _logger.debug("Capturing stdout and stderr")
        super().__enter__()
        self._stdout_context = self.enter_context(contextlib.redirect_stdout(self._stdout))
        # If the next line failed, the stdout context wouldn't exit
        # But this line is very unlikely to fail in practice
        self._stderr_context = self.enter_context(contextlib.redirect_stderr(self._stderr))
        return self

    def __exit__(self: Self, exc_type: type[BaseException], exc_value: BaseException, traceback: TracebackType) -> None:
        _logger.debug("Finished capturing stdout and stderr")
        # The ExitStack handles everything
        super().__exit__(exc_type, exc_value, traceback)


class TestHelper:
    """
    A static singleton with utilities for filesystem operations in tests.
    Use `TestResources.resource` to get a file under `tests/resources/`.

    Initializes a temporary directory with `tempfile.TemporaryDirectory`
    and populates it with a single subdirectory, `TestResources.global_temp_dir`.
    Temp directories for independent tests can be created underneath using
    `TestResources.temp_dir`.
    """

    logger = _logger

    _start_dt = datetime.now(ZoneInfo("Etc/UTC")).astimezone()
    _start_ns = time.monotonic_ns()

    @classmethod
    @contextlib.contextmanager
    def capture(cls: type[Self]) -> Capture:
        """
        Context manager that captures stdout and stderr in a `Capture` object that contains both.
        Useful for testing code that prints to stdout and/or stderr.

        Yields:
            A `Capture` instance, which contains `.stdout` and `.stderr`
        """
        with Capture() as cap:
            yield cap

    @classmethod
    def resource(cls, *nodes: PurePath | str) -> Path:
        """
        Gets a path of a test resource file under `resources/`.

        Arguments:
            nodes: Path nodes under the `resources/` dir

        Returns:
            The Path `resources`/`<node-1>`/`<node-2>`/.../`<node-n>`
        """
        return Path(__package__, "resources", *nodes).resolve()
