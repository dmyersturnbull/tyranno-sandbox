# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Misc. shared code."""

type JsonPrimitive = str | int | float | bool | None
type JsonArray = list[Json]
type JsonLeaf = JsonPrimitive | JsonArray
type JsonBranch = dict[str, Json]  # aka object
type JsonLimb = dict[str, JsonLeaf]
type Json = JsonLeaf | JsonBranch
