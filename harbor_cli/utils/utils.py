"""Utility functions that can't be neatly categorized, or are so niche
that they don't need their own module."""
from __future__ import annotations

import string
from contextlib import contextmanager
from itertools import chain
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import MutableMapping
from typing import NamedTuple
from typing import Optional
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Extra
from rich.text import Text

MappingType = TypeVar("MappingType", bound=MutableMapping[str, Any])


def replace_none(d: MappingType, replacement: Any = "") -> MappingType:
    """Replaces None values in a dict with a given replacement value.
    Iterates recursively through nested dicts and iterables.

    Untested with iterables other than list, tuple, and set.
    """

    if d is None:
        return replacement

    def _try_convert_to_original_type(
        value: Iterable[Any], original_type: type
    ) -> Iterable[Any]:
        """Try to convert an iterable to the original type.
        If the original type cannot be constructed with an iterable as
        the only argument, return a list instead.
        """
        try:
            return original_type(value)
        except TypeError:
            return list(value)

    def _iter_iterable(value: Iterable[Any]) -> Iterable[Any]:
        """Iterates through an iterable recursively, replacing None values."""
        t = type(value)
        v_generator = (item if item is not None else replacement for item in value)
        values = []

        for item in v_generator:
            v = None
            if isinstance(item, MutableMapping):
                v = replace_none(item)
            elif isinstance(item, str):  # don't need to recurse into each char
                v = item  # type: ignore
            elif isinstance(item, Iterable):
                v = _iter_iterable(item)  # type: ignore
            else:
                v = item
            values.append(v)
        if values:
            return _try_convert_to_original_type(values, t)
        else:
            return value

    for key, value in d.items():
        if isinstance(value, MutableMapping):
            d[key] = replace_none(value)
        elif isinstance(value, str):
            d[key] = value
        elif isinstance(value, Iterable):
            d[key] = _iter_iterable(value)
        elif value is None:
            d[key] = replacement
    return d


def iter_submodels(model: BaseModel) -> Iterator[BaseModel]:
    """Iterates recursively over a Pydantic model and returns all submodels."""
    for field, field_info in model.__fields__.items():
        try:
            if field_info.type_ and issubclass(field_info.type_, BaseModel):
                submodel = getattr(model, field)  # type: BaseModel
                yield submodel
                yield from iter_submodels(submodel)
        except TypeError:
            pass


@contextmanager
def forbid_extra(model: BaseModel) -> Iterator[None]:
    """Context manager that temporarily forbids extra fields on a pydantic
    model. Useful for any sort of modifications that require strict checking
    of extra fields, where normally extra fields would be allowed.

    See Also
    --------
    [harbor_cli.utils.iter_submodels][]
    """
    # A list of models and their pre-modification extra settings.
    models = []  # type: list[tuple[BaseModel, Extra]]

    try:
        # Iterate over all submodels in the model + model itself
        for m in chain(iter_submodels(model), [model]):
            original_extra = m.__config__.extra
            models.append((m, original_extra))
            m.__config__.extra = Extra.forbid
        yield
    finally:
        for model, original_extra in models:
            model.__config__.extra = original_extra


class PackageVersion(NamedTuple):
    package: str
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    not_version: Optional[str] = None  # NYI


def parse_version_string(package: str) -> PackageVersion:
    """Parse a PEP 440 package version string into a PackageVersion tuple.

    Must be in the form of <package_name>[{~=,==,!=,<=,>=,<,>}{x.y.z}][,][{~=,==,!=,<=,>=,<,>}{x.y.z}]

    Examples:
        - "foo"
        - "foo==1.2.3"
        - "foo>=1.2.3"
        - "foo>=1.2.3,<=2.3.4"
    """
    # super dumb parsing, no regex for now
    parts = package.replace(" ", "").split(",")
    if len(parts) > 2:
        raise ValueError("Invalid package version string")
    package_name = parts[0]
    min_version = None
    max_version = None
    not_version = None  # noqa # NYI

    operators = ["~=", "==", "<=", ">=", "<", ">"]  # no != for now

    p0 = parts[0]
    for op in operators:
        if op not in p0:
            continue
        package_name, version = p0.split(op)
        package_name = package_name.strip(op)
        if op in ["~=", "=="] and op in p0:
            return PackageVersion(
                package_name, min_version=version, max_version=version
            )
        elif op in ["<=", "<"] and op in p0:
            max_version = version
            break
        elif op in [">=", ">"] and op in p0:
            min_version = version
            break
    if len(parts) == 1:
        return PackageVersion(
            package_name, min_version=min_version, max_version=max_version
        )

    # max version
    p1 = parts[1]
    if p1 and p1[0] in operators:
        if not any(p1.startswith(op) for op in ["<=", "<"]):
            raise ValueError("Invalid package version string")
        max_version = p1.strip(string.punctuation)
    return PackageVersion(
        package_name, min_version=min_version, max_version=max_version
    )


def markup_as_plain_text(s: str) -> str:
    """Renders a string that might contain markup formatting as a plain text string."""
    return Text.from_markup(s).plain
