# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from types import FrameType


class CallerInfo(NamedTuple):
    """The name and args of a calling function."""

    name: str
    args: dict[str, Any]


def get_caller_info(depth: int) -> CallerInfo:
    """Finds the function name and args for the caller (for `depth == 1`), etc."""
    this_frame = inspect.currentframe()
    if not this_frame:
        msg = "Current frame is unavailable."
        raise AssertionError(msg)
    frame: FrameType = this_frame
    for i in range(depth + 1):  # + 1 for this function
        if not frame.f_back:
            msg = f"Caller of frame {frame} (depth {i} from {this_frame}) is unavailable."
            raise AssertionError(msg)
        frame = frame.f_back
    return CallerInfo(frame.f_code.co_name, dict(frame.f_locals))


@dataclass(frozen=True, slots=True, kw_only=True)
class FunctionError(Exception):
    """An error in fetching data from e.g. PyPi."""

    function: str
    args: dict[str, Any]
    message: str

    @classmethod
    def from_call(cls, message: str, *, depth: int) -> FunctionError:
        name, args = get_caller_info(depth)
        return FunctionError(function=name, args=args, message=message)

    def __str__(self) -> str:
        return f"Error in {self.function} with args {self.args}: {self.message}"
