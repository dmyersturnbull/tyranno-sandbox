# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Utilities for working with nested dicts, using `.` as a subkey delimiter.
See [DotTree][].
"""

import json
import re
from collections import defaultdict
from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import date, datetime, time
from re import Pattern
from typing import Any, ClassVar, Self, TypeGuard, overload

type Primitive = str | int | float | bool | date | datetime | time
type Array = list[Toml]
type Leaf = Primitive | Array
type Branch = dict[str, Toml]
type Limb = dict[str, Leaf]
type Toml = Leaf | Branch

type JsonPrimitive = str | int | float | bool | None
type JsonArray = list[Json]
type JsonLeaf = JsonPrimitive | JsonArray
type JsonBranch = dict[str, Json]
type JsonLimb = dict[str, JsonLeaf]
type Json = JsonLeaf | JsonBranch


@dataclass(frozen=True, slots=True)
class Checker:
    """Utilities to validate."""

    key_pattern: ClassVar[Pattern] = re.compile(r"[\w~&|,;<>+-]+")

    @classmethod
    @overload
    def check(cls, node: Branch, /) -> Branch: ...

    @classmethod
    @overload
    def check(cls, node: Array, /) -> Array: ...

    @classmethod
    @overload
    def check(cls, node: Primitive, /) -> Primitive: ...

    @classmethod
    def check(cls, node: Toml, /) -> Toml:
        if isinstance(node, dict | list):
            cls.check_keys(node)
            cls.check_values(node)
        else:
            cls.check_primitive(node)
        return node

    @classmethod
    @overload
    def check_keys(cls, node: Branch, /) -> Branch: ...

    @classmethod
    @overload
    def check_keys(cls, node: Array, /) -> Array: ...

    @classmethod
    def check_keys(cls, node: Branch | Array, /) -> Branch | Array:
        """Recursively, verifies that keys are `str` that don't contain `.`."""
        if isinstance(node, list):
            for v in node:
                if isinstance(v, list | dict):
                    cls.check_keys(v)
        elif isinstance(node, dict):
            if bad := [k for k in node if not isinstance(k, str)]:
                msg = f"Key(s) {bad} are not strings"
                raise ValueError(msg)
            if bad := [k for k in node if "." in k]:
                msg = f"Key(s) {bad} contain '.'"
                raise ValueError(msg)
            for v in node.values():
                if isinstance(v, dict):
                    cls.check_keys(v)
        return node

    @classmethod
    @overload
    def check_values(cls, node: Branch, /) -> Branch: ...

    @classmethod
    @overload
    def check_values(cls, node: Array, /) -> Array: ...

    @classmethod
    def check_values(cls, node: Branch | Array, /) -> Branch | Array:
        """Recursively, verifies that values have valid types."""
        if isinstance(node, list):
            for v in node:
                if isinstance(v, list | dict):
                    cls.check_values(v)
        elif isinstance(node, dict):
            if bad := {k: type(v) for k, v in node.items() if not cls.check_primitive(v)}:
                msg = f"Key(s) {bad.keys()} have invalid values of type(s) {set(bad.values())}"
                raise ValueError(msg)
            for v in node.values():
                if isinstance(v, dict):
                    cls.check_values(v)
        return node

    @classmethod
    def check_primitive[T](cls, value: T, /) -> T:
        if not cls.is_primitive(value):
            msg = f"Invalid type {type(value)}"
            raise TypeError(msg)
        return value

    @classmethod
    def is_primitive(cls, value: Any, /) -> TypeGuard[Primitive]:  # noqa: ANN401
        return isinstance(value, str | int | float | bool | date | datetime | time)


class Utils:
    """Utilities for working with nested dicts."""

    @classmethod
    def nest(cls, items: Branch, /) -> Branch:
        """
        Converts a dict with dotted keys to a nested dict.
        However, won't complain if `items` contains nested items.

        Examples:
            >>> from tyranno_sandbox.dot_tree import Utils
            >>> Utils.nest({"genus.species": "bat"})
            {"genus": {"species": "bat"}}
        """
        dct = {}
        cls._nest(dct, "", items)
        return dct

    @classmethod
    def _nest(cls, to: Branch, at: str, items: Toml) -> None:
        if "." in at:
            k0, k1 = at.split(".", 1)
            if k0 not in to:
                to[k0] = {}
            cls._nest(to[k0], k1, items)
        elif isinstance(items, dict):  # can only happen with mixed input
            if at not in to:
                to[at] = {}
            for k, v in items.items():
                cls._nest(to[at], k, v)
        elif isinstance(items, list):
            if at in to:
                msg = f"Duplicate key {at}"
                raise ValueError(msg)
            to[at] = []
            for v in items:
                cls._nest(to, at, v)
        elif isinstance(to[at], list):
            to[at].append(items)
        elif at in to:
            msg = f"Duplicate key {at}"
            raise ValueError(msg)
        else:
            to[at] = items

    @classmethod
    def dotify(cls, items: Branch, /) -> Branch:
        """
        Converts a nested dict to a dict with dotted keys.
        However, won't complain if a key in (or nested in) `items` contains `.`.

        Examples:
            >>> from tyranno_sandbox.dot_tree import Utils
            >>> Utils.dotify({"genus": {"species": "bat"}})
            {"genus.species": "bat"}
        """
        return dict(cls._dotify("", items))

    @classmethod
    @overload
    def _dotify(cls, at: str, items: Branch) -> Generator[tuple[str, Leaf]]: ...

    @classmethod
    @overload
    def _dotify(cls, at: str, items: Leaf) -> Generator[Leaf]: ...

    @classmethod
    def _dotify(cls, at: str, items: Branch | Array) -> Generator[tuple[str, Leaf] | Leaf]:
        if isinstance(items, dict):
            for k, v in items.items():
                nxt = f"{at}.{k}" if not at else k
                yield from cls._dotify(nxt, v)
        elif isinstance(items, list):
            yield at, [cls._dotify("", v) for v in items]
        elif not at:
            yield items
        else:
            yield at, items


class DotTree(dict[str, Toml]):
    """
    A dictionary with TOML data types, with methods to access nested values via e.g. `animal.species.name`.
    Keys must be strings and cannot contain `.`, which is reserved for nested access.

    Designed with JSON, YAML, and especially TOML in mind.
    The [tyranno_sandbox.dot_tree.Primitive][] type includes the TOML-native `date`, `datetime`, and `time`.
    JSON and YAML do not natively understand these types.
    This class's philosophy is that null/none values should be omitted instead.

    Static factory methods:
        - `from_toml`: Parses a TOML string.
        - `from_nested`: Same as the constructor, but checks the keys.
        - `from_dotted`: Takes, e.g.`{"info.pet.genus": "Felis", "info.pet.species": "catus"}`.
        - `from_mixed`: Can take a mixture of nested and dotted (uncommonly needed).

    General access:
        - `access`: Returns a value, or raises a `KeyError`.
        - `get`: Returns a value, or `None`/default.

    Subtree access:
        - `access_subtree`: Returns an inner tree; e.g. `tree.access_subtree("owner.friends")`.
        - `get_subtree`: Falls back to `{}`/default.

    Primitive value access:
        - `access_value`: Checks that the type is a primitive.
        - `get_value`: Falls back to `None`/default.
        - `access_value_as`: Checks the type.
        - `get_value_as`: ...

    List access:
        - `access_list`: Equivalent to `access_as("key", list)`.
        - `get_list`: Falls back to `[]`/default
        - `access_list_as`: Checks the list element types.
        - `get_list_as`: ...

    Traversal methods:
        - `walk`: Iterates over branches and leaves, depth-first.
        - `limbs`: Maps each bottom-level branch to a dict of its leaves;
            e.g. `{"info.pet": {"genus": "Felis", "species": "catus"}}`.
        - `leaves`: Returns a `dict[str, TomlLeaf]`;
            e.g. `{"info.pet.genus": "Felis", "info.pet.species": "catus"}`.

    Other methods:
        - `normalize`: Drops empty branches.
        - `transform_leaves`: Applies a function `(key, leaf) -> leaf`.
          Be aware that any empty branches will be discarded.
    """

    def __init__(self, /, x: Branch) -> None:
        """Constructs a tree from a nested dict (approximately identical to `dict(x)`)."""
        if not isinstance(x, dict):
            msg = f"Not a dict; actually {type(x)} (value: '{x}')"
            raise TypeError(msg)
        super().__init__(x)

    @classmethod
    def from_mixed(cls, x: Branch, /) -> Self:
        """
        Builds from a potential mixture of nested and `"."`-separated keys.

        Raises:
            TypeError: If `x` is not a `dict` or a key is not a `str`.
            ValueError: If a value (nested) is `None`.

        Examples:
            >>> from tyranno_sandbox.dot_tree import DotTree
            >>> DotTree.from_mixed({"books": [{"title": "Bats", "ids.isbn": "123-4-56-123456-0"}]})
            {"books": [{"title": "Bats", "ids": {"isbn": "123-4-56-123456-0"}}]}
        """  # noqa: DOC502
        return cls(Utils.nest(Utils.dotify(x)))

    @classmethod
    def from_nested(cls, x: Branch, /) -> Self:
        """
        Creates a tree from a nested dict.
        In contrast to the constructor, this verifies that the keys are valid.

        Raises:
            ValueError: If a key contains `.`.
            TypeError: If or `x` is not a `dict`, a key is not a `str`, or a value is `None`.
        """  # noqa: DOC502
        return cls(Checker.check(x))

    @classmethod
    def from_dotted(cls, x: Limb, /) -> Self:
        """
        Creates a new tree from a dict of leaves.

        Raises:
            ValueError: If `x` contains a `dict`; i.e. if there is nesting.
            TypeError: If or `x` is not a `dict` or a key is not a `str`.

        Examples:
            >>> from tyranno_sandbox.dot_tree import DotTree
            >>> DotTree.from_dotted({"owner.name.first": "John"})
            {"owner": {"name": {"first": "John"}}}
            >>> DotTree.from_dotted({"books": [{"title": "Bats", "ids.isbn": "123-4-56-123456-0"}]})
            {"books": [{"title": "Bats", "ids": {"isbn": "123-4-56-123456-0"}}]}
        """  # noqa: DOC502
        return cls(Utils.nest(x))

    def transform_leaves(self, fn: Callable[[str, Leaf], Leaf | None], /) -> Self:
        """
        Applies a function to each leaf, returning a new tree.

        Arguments:
            fn: Returns a new `Leaf`, or `None` to drop the leaf.

        Note:
            If this tree incorrectly contains `None` leaves, they will also be dropped.
            `None` list elements will not be caught.

        Warning:
            Empty branches (`{}`) after the transormation are dropped.
            `dot_dict.transform_leaves(lambda v: v)` is equivalent to [normalize][].
        """
        x = {k: fn(k, v) for k, v in self.leaves()}
        return self.__class__.from_dotted({k: v for k, v in x.items() if v is not None})

    def normalize(self) -> Self:
        """Removes all empty branches."""
        return self.__class__.from_dotted(self.leaves())

    def walk(self) -> Generator[Toml]:
        """Iterates over the branches and leaves, depth-first."""
        for value in self.values():
            if isinstance(value, dict):
                yield from self.__class__(value).walk()
            else:
                yield value

    def limbs(self) -> dict[str, Limb]:
        """
        Maps each bottom-level branch to a dict of its leaves.
        Leaves directly under the root are assigned to key `""`.

        Returns:
            `dotted-keys:str -> (single-key:str -> value)`
        """
        dicts = defaultdict(dict)
        for k, v in self.leaves().items():
            k0, _, k1 = str(k).rpartition(".")
            dicts[k0][k1] = v
        return dicts

    def leaves(self) -> Limb:
        """
        Gets the leaves in this tree; e.g. `{"info.pet.genus": "Felis", "info.pet.species": "catus"}`.

        Warning:
            A `DotTree` can contain empty branches (`{}`), which this method ignores.
        """
        dct = {}
        for key, value in self.items():
            if isinstance(value, dict):
                dct.update({key + "." + k: v for k, v in self.__class__(value).leaves().items()})
            else:
                dct[key] = value
        return dct

    def access_subtree(self, keys: str, /) -> Self:
        """
        Returns the subtree under the `.`-delimited key string, `keys`.

        Raises:
            TypeError: If the value is not a dict.
            KeyError: If `keys` is not found.
        """  # noqa: DOC502
        return self.__class__(self._access(keys))

    def get_subtree(self, keys: str, /, default: Branch | None = None) -> Self:
        """
        Returns the subtree under the `.`-delimited key string, `keys`.
        If `keys` is not found, returns `default`; returns `{}` if `default=None`.

        Raises:
            TypeError: If the value is not a dict.
        """  # noqa: DOC502
        try:
            x = self._access(keys)
        except KeyError:
            x = {} if default is None else default
        return self.__class__(x)

    @overload
    def get_primitive_as[T: Primitive](self, keys: str, /, as_type: type[T], default: T) -> T: ...

    def get_primitive_as[T: Primitive](self, keys: str, /, as_type: type[T], default: T | None = None) -> T:
        """
        Returns a primitive value after checking its type, or `default` if not found.

        Raises:
            TypeError: If not `isinstance(value, as_type)`.
        """
        try:
            x = self._access(keys)
        except KeyError:
            return default
        if not isinstance(x, as_type):
            msg = f"Value {x} from {keys} is a {type(x)}, not {as_type}"
            raise TypeError(msg)
        return x

    def access_primitive_as[T: Primitive](self, keys: str, /, as_type: type[T]) -> T:
        """
        Returns a value after checking its type, or raises a `KeyError` if not found.

        Raises:
            KeyError: If `keys` is not found.
            TypeError: If not `isinstance(value, as_type)`.
        """  # noqa: DOC502
        x = self._access(keys)
        if not isinstance(x, as_type):
            msg = f"Value {x} from {keys} is a {type(x)}, not {as_type}"
            raise TypeError(msg)
        return x

    def get_list(self, keys: str, /, default: Array | None = None) -> Array:
        """
        Returns a list, or `default` if not found.
        `default=None` is equivalent to `default=[]`.

        Raises:
            TypeError: If not `isinstance(value, as_type)`.
        """
        try:
            v = self._access(keys)
        except KeyError:
            return [] if default is None else default
        if not isinstance(v, list):
            msg = f"Value from key {keys} is not a list"
            raise TypeError(msg)
        return v

    def get_list_as[T: Primitive](self, keys: str, /, as_type: type[T], default: list[T] | None = None) -> list[T]:
        """
        Returns a list, or `default` if not found, checking the types of the list elements.
        `default=None` is equivalent to `default=[]`.

        Raises:
            TypeError: If not `isinstance(value, as_type)` for all values in the list.
        """
        try:
            x = self._access(keys)
        except KeyError:
            return [] if default is None else default
        if not isinstance(x, list):
            msg = f"Value from key {keys} is not a list"
            raise TypeError(msg)
        if bad := [y for y in x if not isinstance(y, as_type)]:
            msg = f"Values from key {keys} are not {as_type}: '{bad}'"
            raise TypeError(msg)
        return x

    def access_list_as[T: Primitive](self, keys: str, /, as_type: type[T]) -> list[T]:
        """
        Returns a list after checking the types of its elements, or raises a `KeyError`.

        Raises:
            KeyError: If `keys` is not found.
            TypeError: If not `isinstance(value, as_type)` for all values in the list.
        """  # noqa: DOC502
        x = self._access(keys)
        if not isinstance(x, list):
            msg = f"Value {x} is not a list for key {keys}"
            raise TypeError(msg)
        if not all(isinstance(y, as_type) for y in x):
            msg = f"Value {x} from {keys} is a {type(x)}, not {as_type}"
            raise TypeError(msg)
        return x

    @overload
    def get_primitive[T: Primitive](self, keys: str, /, default: T) -> T: ...

    def get_primitive[T: Primitive](self, keys: str, /, default: T | None = None) -> T | None:
        """
        Returns a primitive value, or `default` if not found.

        Raises:
            TypeError: If the value is not a primitive.
        """  # noqa: DOC502
        try:
            v = self._access(keys)
        except KeyError:
            return default
        return Checker.check_primitive(v)

    def access_primitive(self, keys: str) -> Primitive:
        """
        Returns a primitive value, or raises a `KeyError`.

        Raises:
            KeyError: If the key is not found.
            TypeError: If the value is not a primitive.
        """  # noqa: DOC502
        return Checker.check_primitive(self._access(keys))

    def get(self, keys: str) -> Toml | None:
        """Returns a value from the `.`-delimited `keys`, falling back to `None`."""
        try:
            return self._access(keys)
        except KeyError:
            return None

    def access(self, keys: str) -> Toml:
        """
        Returns a value from the `.`-delimited `keys`, or raises a `KeyError`.

        Raises:
            KeyError: If the key is not found.
        """  # noqa: DOC502
        return self._access(keys)

    def _access(self, keys: str) -> Toml:
        x = self
        split = keys.split(".")
        for i, k in enumerate(split):
            try:
                x = x[k]
            except KeyError:
                msg = f"No such key '{'.'.join(split[:i])}<<{k}>>{keys[i + 1 :]}'"
                raise KeyError(msg) from None
        return x

    def __rich_repr__(self) -> str:
        """Pretty-prints for [Rich](https://github.com/Textualize/rich) via [print][]."""
        return self.print()

    def print(self) -> str:
        """Pretty-prints the leaves of this dict using `json.dumps`."""
        return json.dumps(self, ensure_ascii=True, indent=2)


class DotTrees:
    """Static factory methods for `DotTree`."""

    @classmethod
    def from_json(cls, data: str, /) -> DotTree:
        """Builds a tree from a JSON string."""
        import json

        return DotTree.from_nested(json.loads(data))

    @classmethod
    def from_toml(cls, data: str, /) -> DotTree:
        """Builds a tree from a TOML string, parsed with `tomllib`."""
        import tomllib

        return DotTree.from_nested(tomllib.loads(data))

    @classmethod
    def to_json(cls, tree: DotTree) -> str:
        """Converts to JSON, raising `ValueError` for `NaN`, `Inf`, and `-Inf` values."""
        import json

        return json.dumps(tree, ensure_ascii=False, allow_nan=False)
