# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Utility to create custom JMESPath functions."""

import inspect
from collections.abc import Callable
from typing import Any, Final, get_type_hints

from jmespath.functions import Functions, signature

# Mapping of Python -> JMESPath types.
TYPE_MAP: Final[dict[type, str]] = {
    str: "string",
    int: "number",  # JMESPath only has `number`.
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    Any: "any",
}


class JmesFunctionsFactory:
    """Factory for JMESPath functions."""

    def register_class[T](self, class_: type[T]) -> type[Functions]:
        """Registers the methods defined in `class_` as JMESPath functions.

        Methods whose names start with `_` are ignored.
        Copies methods from `class_` to a new class that inherits `jmespath.functions.Functions`.
        """
        members = inspect.getmembers(class_, predicate=inspect.isfunction)
        methods = {name: method for name, method in members if not name.startswith("_")}
        namespace = {}
        for name, method in methods.items():
            jmes_name = f"_func_{name}"
            namespace[jmes_name] = self._register_method(method, name)
        # Dynamically create a subclass of jmespath.functions.Functions.
        # noinspection PyTypeChecker
        return type(f"{class_.__name__}JmesFunctions", (Functions,), namespace)

    def _register_method[**P, V](self, method: Callable[P, V], name: str) -> Callable[P, V]:
        sig = inspect.signature(method)
        type_hints = get_type_hints(method)
        param_specs = [{"types": TYPE_MAP[type_hints[p.name]]} for p in sig.parameters.values()]

        def make_wrapped(m: Callable[P, V]) -> Callable[P, V]:
            return lambda _self, *args: m(*args)

        wrapped = make_wrapped(method)
        wrapped.__name__ = f"_func_{name}"
        return signature(*param_specs)(wrapped)
