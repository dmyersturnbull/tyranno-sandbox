# SPDX-FileCopyrightText: Copyright 2020-2026, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Custom JSONPath functions."""

from __future__ import annotations

from dataclasses import dataclass
from operator import itemgetter
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from niquests import Session

    from tyranno_sandbox._core import Json, JsonBranch


class LicenseDict(TypedDict):
    id: str
    spdx_id: str
    name: str
    uri: str
    links: list[str]
    header: str
    text: str


@dataclass(frozen=True, slots=True)
class LicenseFunctions:
    session: Session

    def license_data(self, spdx_id: str) -> LicenseDict:
        data = self._dl_license(spdx_id)
        uris = self._get_license_uris(data)
        return LicenseDict(
            id=spdx_id,
            spdx_id=spdx_id,
            name=data["name"],
            uri=f"https://spdx.org/licenses/{spdx_id}.html",
            links=uris,
            header=f"SPDX-License-Identifier: {spdx_id}",
            text=data["licenseText"],
        )

    def _dl_license(self, spdx_id: str) -> Json:
        dir_ = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/details"
        url = f"{dir_}/{spdx_id}.json"
        response = self.session.get(url).raise_for_status()
        return response.json()

    def _get_license_uris(self, data: JsonBranch) -> list[str]:
        urls = (u for u in data["crossRef"] if u.get("isValid") and u.get("isLive"))
        urls = sorted(urls, key=itemgetter("order"))
        # noinspection HttpUrlsUsage
        return [u["url"].replace("http://", "https://") for u in urls]
