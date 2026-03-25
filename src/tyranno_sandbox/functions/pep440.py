# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar, Literal, TypedDict

from packaging.version import Version as Pep440

from tyranno_sandbox.functions._core import FunctionError


class Pep440Dict(TypedDict):
    full_version: str
    normalized_version: str
    public_version: str
    major_version: str
    minor_version: str
    micro_version: str
    epoch: int
    major: int
    minor: int
    micro: int
    patch: int
    pre: str
    dev: str
    post: str
    pre_type: str  # `""` if none
    pre_number: int | Literal[""]
    dev_number: int | Literal[""]
    post_number: int | Literal[""]


class Pep440SpecDict(TypedDict):
    package: str
    predicate: str


@dataclass(frozen=True, slots=True)
class Pep440Functions:
    PEP440_PRE_STRS: ClassVar = {"alpha": "a", "beta": "b", "c": "rc", "pre": "rc", "preview": "rc"}
    PEP440_SPEC_RE: ClassVar = re.compile(r"""([A-Za-z0-9_-]++)(.++)""")

    def of(self, v: Pep440 | str) -> Pep440Dict:
        if isinstance(v, str):
            v = Pep440(v)
        major_ver = f"{v.epoch}!{v.major}" if v.epoch else str(v.major)
        minor_ver = f"{major_ver}.{v.minor}"
        return Pep440Dict(
            full_version=self.sanitize(v),
            normalized_version=self.normalize(v),
            public_version=v.public,
            major_version=major_ver,
            minor_version=minor_ver,
            micro_version=v.base_version,
            epoch=v.epoch,
            major=v.major,
            minor=v.minor,
            patch=v.micro,
            micro=v.micro,
            pre=f"{v.pre[0]}{v.pre[1]}" if v.pre is not None else "",
            dev=f"dev{v.dev}" if v.dev is not None else "",
            post=f"post{v.post}" if v.post is not None else "",
            pre_type=v.pre[0] if v.pre is not None else "",
            pre_number=v.pre[1] if v.pre is not None else "",
            dev_number=v.dev if v.dev is not None else "",
            post_number=v.post if v.post is not None else "",
        )

    def sanitize(self, v: Pep440 | str) -> str:
        if isinstance(v, str):
            v = Pep440(v)
        has_pre = v.pre is not None
        has_post = v.post is not None
        has_dev = v.dev is not None
        if sum((has_pre, has_post, has_dev)):
            msg = f"PyPa package version {v} mixes pre, post, and/or dev numbers."
            raise FunctionError.from_call(msg, depth=2)
        epoch = f"{v.epoch}!" if v.epoch else ""
        main = f"{v.major}.{v.minor}.{v.micro}"
        pre = f"-{v.pre[0]}{v.pre[1]}" if has_pre else ""
        dev = f"-dev{v.dev}" if has_dev else ""
        post = f"-post{v.post}" if has_post else ""
        return epoch + main + pre + dev + post

    def normalize(self, v: Pep440 | str, *, force_epoch: bool = False) -> str:
        if isinstance(v, str):
            v = Pep440(v)
        has_pre = v.pre is not None
        has_post = v.post is not None
        has_dev = v.dev is not None
        main = f"{v.major}.{v.minor}.{v.micro}"
        epoch = f"{v.epoch}!" if v.epoch or force_epoch else ""
        if has_pre and v.pre[0] not in self.PEP440_PRE_STRS:
            msg = f"PyPa package version {v} has an unrecognized prerelease type {v.pre[0]}."
            raise FunctionError.from_call(msg, depth=2)
        # The normal-form separators are '' for pre, '-' for dev, and '-' for post.
        pre = self.PEP440_PRE_STRS[v.pre[0]] + str(v.pre[1]) if has_pre else ""
        post = f".post{v.post}" if has_post else ""
        dev = f".dev{v.dev}" if has_dev else ""
        return epoch + main + pre + dev + post

    def split_spec(self, spec: str) -> tuple[str, str]:
        if m := self.PEP440_SPEC_RE.fullmatch(spec):
            return m.group(1), m.group(2)
        raise ValueError(spec)

    def max_per(self, versions: list[str], per: str) -> list[str]:
        versions = [Pep440(v) for v in versions]
        options = {"major", "minor", "micro"}
        if per not in options:
            msg = f"Argument '{per}' is not one of {options}."
            raise FunctionError.from_call(msg, depth=1)
        best = {}
        for v in versions:
            v0 = getattr(v, per)
            if v0 not in best or v > best[v0]:
                best[v0] = v
        return [self.sanitize(b) for b in best.values()]
