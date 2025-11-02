# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Utilities for tests."""

import logging
import time
from contextlib import ExitStack, contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Final, Self, override
from zoneinfo import ZoneInfo

from hypothesis import settings as hyp

if TYPE_CHECKING:
    from collections.abc import Generator
    from os import PathLike
    from types import TracebackType

__all__ = ["Helper", "logger"]

ETC_UTC: Final = ZoneInfo("Etc/UTC")
TESTS_ROOT: Final = Path(__file__).parent.resolve()  # .relative_to(Path.cwd())
PROJECT_ROOT: Final = TESTS_ROOT.parent.resolve()  # .relative_to(Path.cwd())
# Separate logging in the main package vs. inside test functions.
logger = logging.getLogger(f"{PROJECT_ROOT.name}::test")

# Configure Hypothesis.
# Only passing args that differ from the original (or parent).
# `ci` is predefined (and used in CI), but we'll override it.
# `more` uses 10x the examples and 2x the deadline; even more uses 100x/4x.
# Note: omitting `parent=` would derive from the **current** profile.
hyp.register_profile("ci", parent=hyp.get_profile("ci"), derandomize=False, print_blob=False)
hyp.register_profile("more", parent=hyp.get_profile("default"), max_examples=1_000, deadline=400)
hyp.register_profile(
    "even-more", parent=hyp.get_profile("default"), max_examples=10_000, deadline=800
)

# Print some info.
logger.debug("Tests root: %s", TESTS_ROOT)
logger.debug("Hypothesis max_examples = %i", hyp().max_examples)
logger.debug("Hypothesis deadline = %f s", hyp().deadline.total_seconds())
logger.debug("Hypothesis derandomize = %s", hyp().derandomize)
logger.debug("Hypothesis suppress_health_check = %s", hyp().suppress_health_check)
logger.debug("Hypothesis phases = %s", ",".join(p.name for p in hyp().phases))


class Capture(ExitStack):
    """A context manager that captures standard out and error streams.

    Notes:
        Logging is unaffected; if stderr is a handler, [stderr][] will include logging statements.

    Example:
        ```python
        with Capture() as cap:
            print("out")
            print("error", file=sys.stderr)
            stdout = cap.stdout
            stderr = cap.stderr
        ```
    """

    def __init__(self) -> None:
        super().__init__()
        self._stdout = StringIO()
        self._stderr = StringIO()

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
        self._stdout_context = self.enter_context(redirect_stdout(self._stdout))
        # If the next line failed, the stdout context wouldn't exit
        # But this line is very unlikely to fail in practice
        self._stderr_context = self.enter_context(redirect_stderr(self._stderr))
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        logger.debug("Finished capturing stdout and stderr")
        # The ExitStack handles everything
        super().__exit__(exc_type, exc_value, exc_tb)


@dataclass(frozen=True, slots=True)
class Start:
    """Start times for a test helper.

    Contains a monotonic clock time, a local datetime, and the local datetime converted to UTC.
    The timestamps are safe to use in filesystem paths.
    They're valid under ISO 8601 but not RFC 3339:

    - UTC: `YYYY-MM-DD'T'hhmmss.µµµµµµ'Z'`,
    - local `YYYY-MM-DD'T'hhmmss.µµµµµµ[+-]hhmm[ss]`.
    """

    mono_ns: int
    local: datetime
    utc: datetime = field(init=False, repr=False, hash=False)
    local_str: str = field(init=False, repr=False, hash=False)
    utc_str: str = field(init=False, repr=False, hash=False)

    @classmethod
    def new(cls) -> Self:
        return cls(mono_ns=time.monotonic_ns(), local=datetime.now().astimezone())

    def __post_init__(self) -> None:
        object.__setattr__(self, "utc", self.local.astimezone(ETC_UTC))
        object.__setattr__(self, "local_str", self.local.strftime("%Y-%m-%dT%H%M%S.%f%z"))
        object.__setattr__(self, "utc_str", self.local.strftime("%Y-%m-%dT%H%M%S.%fZ"))

    @property
    def ns_elapsed(self) -> int:
        return time.monotonic_ns() - self.mono_ns

    @property
    def time_elapsed(self) -> timedelta:
        return timedelta(microseconds=self.ns_elapsed / 1000)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}@{self.local_str}"


@dataclass(frozen=True, slots=True, kw_only=True)
class Helper:
    """A set of utilities for tests classes.

    Use [resource][] to get a file under `tests/resources/`.
    """

    start: Start

    @classmethod
    def new(cls) -> Self:
        return cls(start=Start.new())

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(start={self.start})"

    @contextmanager
    def capture(self) -> Generator[Capture]:
        """Context manager that captures stdout and stderr in a `Capture` object that contains both.

        Yields:
            A [Capture][] instance, which contains `.stdout` and `.stderr`.
        """
        with Capture() as cap:
            yield cap

    def resource(self, *nodes: PathLike | str) -> Path:
        """Gets a path of a test resource file under `tests/resources/`.

        Arguments:
            nodes: Path nodes under `tests/resources/`.

        Returns:
            The Path `tests`/`resources`/`<node-1>`/.../`<node-n>`, relative to the CWD.
        """
        return Path(TESTS_ROOT, "resources", *nodes)
