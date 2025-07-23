# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Utilities for working with nested dicts, using `.` as a subkey delimiter.

See [DotTree][].
"""

import re
from collections import Counter, defaultdict
from collections.abc import Callable, Generator, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time
from re import Pattern
from typing import Final, Literal, Self, TypeGuard, overload

try:
    import orjson as json
except ImportError:
    import json

type Primitive = str | int | float | bool | date | datetime | time
type Array = list[Toml]
type Leaf = Primitive | Array
type Branch = dict[str, Toml]
type Limb = dict[str, Leaf]
type Toml = Leaf | Branch

__all__ = [
    "Array",
    "Branch",
    "Checker",
    "DotTree",
    "DotTrees",
    "Leaf",
    "LeafConflictError",
    "LeafIntersectionError",
    "LeavesInCommonError",
    "Limb",
    "Primitive",
    "Toml",
    "Utils",
]


@dataclass(frozen=True, slots=True)
class DuplicateKeyError(Exception):
    """A key was defined more than once."""

    key: str

    def __str__(self) -> str:
        return f"Key '{self.key}' was defined more than once."


@dataclass(frozen=True, slots=True)
class LeavesInCommonError(Exception):
    """Two or more trees have leaves in common."""


@dataclass(frozen=True, slots=True)
class LeafIntersectionError(LeavesInCommonError):
    """There are leaves in common between two or more trees."""

    intersection: dict[str, list[Leaf]]
    msg: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        msg = "??"
        if j := self.intersection:
            n_intersect = str(len(j)) + " leaves are" if len(j) > 1 else " leaf is"
            intersect = "{ " + ", ".join(j.keys()) + " }"
            msg = f"{n_intersect} present in multiple trees: {intersect}."
            if conflicts := {k: v for k, v in j.items() if len(set(v)) > 1}:
                conflict_str = ", ".join(f"{k}: {'/'.join(v)}" for k, v in conflicts.items())
                n_conflict = str(len(conflicts)) + ("have" if len(conflicts) > 1 else "has")
                msg += f" {n_conflict} conflicting values: {conflict_str}."
        object.__setattr__(self, "msg", msg)

    def __str__(self) -> str:
        return self.msg


@dataclass(frozen=True, slots=True)
class LeafConflictError(LeavesInCommonError):
    """There are leaves with different values in common between two or more trees."""

    intersection: dict[str, list[Leaf]]
    msg: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        msg = "??"
        if self.intersection:
            clashes = {k: v for k, v in self.intersection.items() if len(set(v)) > 1}
            n_clash = str(len(clashes)) + (" leaves are" if len(clashes) > 1 else " leaf is")
            clash_list = ", ".join(f"{k}: {'/'.join(v)}" for k, v in clashes.items())
            msg = f"{n_clash} are present with clashing values in multiple trees: {clash_list}"
        object.__setattr__(self, "msg", msg)

    def __str__(self) -> str:
        return self.msg


@dataclass(frozen=True, slots=True, kw_only=True)
class Checker:
    """Utilities to validate."""

    key_pattern: Pattern[str] = re.compile(r"[\w~&|,;<>+-]+")

    @overload
    def check(self, node: Branch, /) -> Branch: ...

    @overload
    def check(self, node: Array, /) -> Array: ...

    @overload
    def check(self, node: Primitive, /) -> Primitive: ...

    def check(self, node: Toml, /) -> Toml:
        if isinstance(node, dict | list):
            self.check_keys(node)
            self.check_values(node)
        else:
            self.check_primitive(node)
        return node

    @overload
    def check_keys(self, node: Branch, /) -> Branch: ...

    @overload
    def check_keys(self, node: Array, /) -> Array: ...

    def check_keys(self, node: Branch | Array, /) -> Branch | Array:
        """Recursively verifies that keys are `str`, don't contain `.`, and match `key_pattern`."""
        if isinstance(node, list):
            for v in node:
                if isinstance(v, list | dict):
                    self.check_keys(v)
        elif isinstance(node, dict):
            if bad := [k for k in node if not isinstance(k, str)]:
                # noinspection PyUnboundLocalVariable
                msg = f"Key(s) {bad} are not strings."
                raise ValueError(msg)
            if bad := [k for k in node if "." in k]:
                msg = f"Key(s) {bad} contain '.'."
                raise ValueError(msg)
            for v in node.values():
                if isinstance(v, dict):
                    self.check_keys(v)
            if bad := [k for k in node if not self.key_pattern.fullmatch(k)]:
                msg = f"Key(s) {bad} do not match pattern '{self.key_pattern}'."
                raise ValueError(msg)
        return node

    @overload
    def check_values(self, node: Branch, /) -> Branch: ...

    @overload
    def check_values(self, node: Array, /) -> Array: ...

    def check_values(self, node: Branch | Array, /) -> Branch | Array:
        """Recursively, verifies that values have valid types."""
        if isinstance(node, list):
            for v in node:
                if isinstance(v, list | dict):
                    self.check_values(v)
        elif isinstance(node, dict):
            if bad := {k: type(v) for k, v in node.items() if not self.check_primitive(v)}:
                # noinspection PyUnboundLocalVariable
                msg = f"Key(s) {bad.keys()} have invalid values of type(s) {set(bad.values())}"
                raise ValueError(msg)
            for v in node.values():
                if isinstance(v, dict):
                    self.check_values(v)
        return node

    def check_primitive[T](self, value: T, /) -> T:
        if not self.is_primitive(value):
            msg = f"Invalid type {type(value)}"
            raise TypeError(msg)
        return value

    def is_primitive(self, value: Toml, /) -> TypeGuard[Primitive]:
        return isinstance(value, str | int | float | bool | date | datetime | time)


@dataclass(frozen=True, slots=True, kw_only=True)
class Utils:
    """Utilities for working with nested dicts."""

    merge_lists: bool = False

    def nest(self, items: Branch, /) -> Branch:
        """Converts a dict with dotted keys to a nested dict.

        However, won't complain if `items` contains nested items.

        Examples:
            >>> from tyranno_sandbox.dot_tree import Utils
            >>> Utils().nest({"genus.species": "bat"})
            {'genus': {'species': 'bat'}}
        """
        out: Branch = {}
        for k, v in items.items():
            self._nest(out, k, v)
        return out

    def _nest(self, dst: Branch, key: str, item: Toml) -> None:
        self._nest_check(dst, key, item)
        if "." in key:
            self._nest_branch(dst, key, item)
        else:
            self._nest_leaf(dst, key, item)

    def _nest_check(self, dst: Branch, key: str, item: Toml) -> None:
        if (found := dst.get(key)) is not None and (
            type(found) is not type(item)
            or type(found) not in {dict, list}
            or (type(found) is list and not self.merge_lists)
        ):
            raise DuplicateKeyError(key)

    def _nest_branch(self, dst: Branch, key: str, item: Toml) -> None:
        head, tail = key.split(".", 1)
        sub = dst.setdefault(head, {})
        if not isinstance(sub, dict):
            raise DuplicateKeyError(head)
        self._nest(sub, tail, item)

    def _nest_leaf(self, dst: Branch, key: str, item: Toml) -> None:
        if isinstance(item, dict):
            node = dst.setdefault(key, {})
            for k, v in item.items():
                self._nest(node, k, v)
        elif isinstance(item, list) and self.merge_lists:
            list_: Array = dst.setdefault(key, [])
            node: Branch = {}
            for v in item:
                self._nest(node, key, v)
            list_ += list(node.values())
        else:
            dst[key] = item

    def dotify(self, items: Branch, /) -> Branch:
        """Converts a nested dict to a dict with dotted keys.

        However, won't complain if a key in (or nested in) `items` contains `.`.

        Examples:
            >>> from tyranno_sandbox.dot_tree import Utils
            >>> Utils().dotify({"genus": {"species": "bat"}})
            {'genus.species': 'bat'}
        """
        return dict(self._dotify("", items))

    def _dotify(self, path: str, item: Toml) -> Generator[tuple[str, Leaf]]:
        if isinstance(item, dict):
            for k, v in item.items():
                new_path = f"{path}.{k}" if path else k
                yield from self._dotify(new_path, v)
        elif isinstance(item, list):
            lst: Leaf = []
            for v in item:
                sub = list(self._dotify("", v))
                lst.append(sub[0] if len(sub) == 1 else dict(sub))
            yield path, lst
        else:
            yield path, item


_UTILS: Final = Utils()
_CHECKER = Checker()


class DotTree(Mapping[str, Toml]):
    """A dict with TOML data types and methods to access nested values via e.g. `pet.name`.

    Keys must be strings and cannot contain `.`, which is reserved for nested access.

    Designed with JSON, YAML, and especially TOML in mind.
    The [tyranno_sandbox.dot_tree.Primitive][] type includes the TOML-native
    `date`, `datetime`, and `time`.
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

    def __iter__(self) -> Iterator[str]:
        return iter(self._raw)

    def __init__(self, /, x: Branch) -> None:
        """Constructs a tree from a nested dict (about the same as `dict(x)`)."""
        if not isinstance(x, dict):
            msg = f"Not a dict; actually {type(x)} (value: '{x}')"
            raise TypeError(msg)
        self._raw = x

    def __getitem__(self, key: str, /) -> Toml:
        return self._raw[key]

    def __len__(self) -> int:
        return len(self._raw)

    @classmethod
    def from_mixed(cls, x: Branch, /) -> Self:
        """Builds from a potential mixture of nested and `"."`-separated keys.

        Raises:
            TypeError: If `x` is not a `dict` or a key is not a `str`.
            ValueError: If a value (nested) is `None`.

        Examples:
            >>> from tyranno_sandbox.dot_tree import DotTree
            >>> DotTree.from_mixed({"books": [{"title": "Bats", "ids.isbn": "123-4-56-123456-0"}]})
            {'books': [{'title': 'Bats', 'ids.isbn': '123-4-56-123456-0'}]}
        """
        return cls(_UTILS.nest(_UTILS.dotify(x)))

    @classmethod
    def from_nested(cls, x: Branch, /) -> Self:
        """Creates a tree from a nested dict.

        In contrast to the constructor, this verifies that the keys are valid.

        Raises:
            ValueError: If a key contains `.`.
            TypeError: If or `x` is not a `dict`, a key is not a `str`, or a value is `None`.
        """
        return cls(_CHECKER.check(x))

    @classmethod
    def from_dotted(cls, x: Limb, /) -> Self:
        """Creates a new tree from a dict of leaves.

        Raises:
            ValueError: If `x` contains a `dict`; i.e. if there is nesting.
            TypeError: If or `x` is not a `dict` or a key is not a `str`.

        Examples:
            >>> from tyranno_sandbox.dot_tree import DotTree
            >>> DotTree.from_dotted({"owner.name.first": "John"})
            {'owner': {'name': {'first': 'John'}}}
            >>> DotTree.from_dotted({"books": [{"title": "Bats", "ids.isbn": "123-4-56-123456-0"}]})
            {'books': [{'title': 'Bats', 'ids.isbn': '123-4-56-123456-0'}]}
        """
        return cls(_UTILS.nest(x))

    def transform_leaves(self, fn: Callable[[str, Leaf], Leaf | None], /) -> Self:
        """Applies a function to each leaf, returning a new tree.

        Arguments:
            fn: Returns a new `Leaf`, or `None` to drop the leaf.

        Note:
            If this tree incorrectly contains `None` leaves, they will also be dropped.
            `None` list elements will not be caught.

        Warning:
            Empty branches (`{}`) after the transformation are dropped.
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
        """Maps each bottom-level branch to a dict of its leaves.

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
        """Gets the leaves in this tree.

        For example: `{"info.pet.genus": "Felis", "info.pet.species": "catus"}`.

        Warning:
            A `DotTree` can contain empty branches (`{}`), which this method ignores.
        """
        dct: Limb = {}
        for key, value in self.items():
            if isinstance(value, dict):
                dct.update({key + "." + k: v for k, v in self.__class__(value).leaves().items()})
            else:
                dct[key] = value
        return dct

    def access_subtree(self, keys: str, /) -> Self:
        """Returns the subtree under the `.`-delimited key string, `keys`.

        Raises:
            TypeError: If the value is not a dict.
            KeyError: If `keys` is not found.
        """
        return self.__class__(self._access(keys))

    def get_subtree(self, keys: str, /, default: Branch | None = None) -> Self:
        """Returns the subtree under the `.`-delimited key string, `keys`.

        If `keys` is not found, returns `default`; returns `{}` if `default=None`.

        Raises:
            TypeError: If the value is not a dict.
        """
        try:
            x = self._access(keys)
        except KeyError:
            x = {} if default is None else default
        return self.__class__(x)

    @overload
    def get_primitive_as[T: Primitive](self, keys: str, /, as_type: type[T], default: T) -> T: ...

    def get_primitive_as[T: Primitive](
        self, keys: str, /, as_type: type[T], default: T | None = None
    ) -> T:
        """Returns a primitive value after checking its type, or `default` if not found.

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
        """Returns a value after checking its type, or raises a `KeyError` if not found.

        Raises:
            KeyError: If `keys` is not found.
            TypeError: If not `isinstance(value, as_type)`.
        """
        x = self._access(keys)
        if not isinstance(x, as_type):
            msg = f"Value {x} from {keys} is a {type(x)}, not {as_type}"
            raise TypeError(msg)
        return x

    def get_list(self, keys: str, /, default: Array | None = None) -> Array:
        """Returns a list, or `default` if not found.

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

    def get_list_as[T: Toml](
        self, keys: str, /, as_type: type[T], default: list[T] | None = None
    ) -> list[T]:
        """Returns a list, or `default` if not found, checking the types of the list elements.

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
            # noinspection PyUnboundLocalVariable
            msg = f"Values from key {keys} are not {as_type}: '{bad}'"
            raise TypeError(msg)
        return x

    def access_list_as[T: Toml](self, keys: str, /, as_type: type[T]) -> list[T]:
        """Returns a list after checking the types of its elements, or raises a `KeyError`.

        Raises:
            KeyError: If `keys` is not found.
            TypeError: If not `isinstance(value, as_type)` for all values in the list.
        """
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
        """Returns a primitive value, or `default` if not found.

        Raises:
            TypeError: If the value is not a primitive.
        """
        try:
            v = self._access(keys)
        except KeyError:
            return default
        return _CHECKER.check_primitive(v)

    def access_primitive(self, keys: str) -> Primitive:
        """Returns a primitive value, or raises a `KeyError`.

        Raises:
            KeyError: If the key is not found.
            TypeError: If the value is not a primitive.
        """
        return _CHECKER.check_primitive(self._access(keys))

    @overload
    def get(self, keys: str, default: Toml = None) -> Toml: ...

    def get(self, keys: str, default: Toml | None = None) -> Toml | None:
        """Returns a value from the `.`-delimited `keys`, falling back to `default`."""
        try:
            return self._access(keys)
        except KeyError:
            return default

    def access(self, keys: str) -> Toml:
        """Returns a value from the `.`-delimited `keys`, or raises a `KeyError`.

        Raises:
            KeyError: If the key is not found.
        """
        return self._access(keys)

    def _access(self, keys: str) -> Toml:
        x: Toml = self._raw
        split = keys.split(".")
        for i, k in enumerate(split):
            if not isinstance(x, dict):
                msg = (
                    f"Value at key '{'.'.join(split[:i])}<<{k}>>{keys[i + 1 :]}'"
                    f" is a {type(x)}, not an object."
                )
                raise TypeError(msg)
            try:
                x = x[k]
            except KeyError:
                msg = f"No such key '{'.'.join(split[:i])}<<{k}>>{keys[i + 1 :]}'."
                raise KeyError(msg) from None
        return x

    def __rich_repr__(self) -> str:
        """Pretty-prints for [Rich](https://github.com/Textualize/rich) via [print][]."""
        return self.print()

    def print(self) -> str:
        """Pretty-prints the leaves of this dict using `json.dumps`."""
        import json  # noqa: PLC0415

        return json.dumps(self, ensure_ascii=False, indent=2)


class DotTrees:
    """Static factory methods for `DotTree`."""

    @classmethod
    def merge_leaves(
        cls,
        *trees: DotTree,
        replace: Literal["always", "if_values_match", "never"] = "if_values_match",
    ) -> DotTree:
        """Builds a tree containing the union of the leaves of `trees`.

        Empty branches are removed, and arrays are **not** merged.

        Args:
            trees: Trees to merge.
            replace: How to handle overlapping keys:
              - `"always"`: Only retain the value from the rightmost tree, discarding any others.
              - `"if_values_match"`: Error if two or more trees have identically named leaves with different values.
              - `"never"`: Error if two or more trees have identically named leaves, even if they have the same value.

        Raises:
            LeafConflictError:
              If `replace` is `same_value` and ≥ 1 key is in ≥ 2 trees with ≥ 2 unique values.
            LeafIntersectionError:
              If `replace` is `never`, and ≥ 1 key is in ≥ 2 trees (ignoring their values).
        """
        limbs = [tree.leaves() for tree in trees]
        if replace == "never" and (intersect := cls.leaf_intersection(*limbs)):
            raise LeafIntersectionError(intersect)
        if (
            replace == "same_value"
            and (intersect := cls.leaf_intersection(*limbs))
            and any(len(set(v)) > 1 for v in intersect.values())
        ):
            raise LeafConflictError(intersect)
        merged: dict[str, Leaf] = {}
        for limb in limbs:
            merged.update(limb)
        return DotTree.from_dotted(merged)

    @classmethod
    def leaf_intersection(cls, *limbs: Limb) -> dict[str, list[Leaf]]:
        """Returns a mapping of each leaf key to its values in `limbs` for keys that 2+ limbs share.

        The length of each list is equal to the number of limbs sharing that key.
        Values are not checked and are not deduplicated.
        """
        all_keys: set[str] = set()
        for limb in limbs:
            all_keys |= limb.keys()
        dict_ = {k: [limb[k] for limb in limbs if k in limb] for k in all_keys}
        return {k: v for k, v in dict_.items() if len(v) > 1}

    @classmethod
    def leaf_intersection_size(cls, *limbs: Limb) -> dict[str, int]:
        """Equivalent to `{k: len(v) for k, v in leaf_intersection(limbs).items()}`.

        This is simply faster than using [leaf_intersection][].
        """
        counts: Counter[str] = Counter()
        for limb in limbs:
            counts.update(limb.keys())
        return dict(counts.most_common())

    @classmethod
    def from_json(cls, data: str | bytes | bytearray, /) -> DotTree:
        """Builds a tree from a JSON string."""
        return DotTree.from_nested(json.loads(data))

    @classmethod
    def from_toml(cls, data: str | bytes | bytearray, /) -> DotTree:
        """Builds a tree from a TOML string, parsed with `tomllib`."""
        import tomllib  # noqa: PLC0415

        if isinstance(data, (bytes, bytearray)):
            data = data.decode()
        return DotTree.from_nested(tomllib.loads(data))

    @classmethod
    def to_json(cls, tree: DotTree, /, *, sort: bool = False) -> str:
        """Converts to JSON, raising `ValueError` for `NaN`, `Inf`, and `-Inf` values."""
        return json.dumps(tree, ensure_ascii=False, allow_nan=False, sort_keys=sort)
