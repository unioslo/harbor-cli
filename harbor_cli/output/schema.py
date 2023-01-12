"""Somewhat experimental schema for (de)serializing data (JSON, YAML, etc.)

Not to be confused with JSON Schema (<https://json-schema.org/specification.html>)

The aim is to be able to serialize a Pydantic model to JSON, YAML, etc. and
include metadata about the model in the output. This metadata can
then be used to deserialize the data back into the correct Pydantic model.

The benefit of this is that we can more easily print the data as tables
using the harborapi.models.BaseModel's as_table() method, and we can also use the
Pydantic models' custom validation, methods and properties. Furthermore,
we avoid the problem of forwards-compatibility of pickling data,
because we can always deserialize the data back into the most up-to-date
version of the data type.

The difference between this and the built-in schema funtionality of Pydantic
is that we are not interested in actually exporting the full schema of all
the models, but rather just enough information to dynamically load the correct
model from the correct location when deserializing the data.
"""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Sequence
from typing import TypeVar
from typing import Union

from pydantic import BaseModel
from pydantic import root_validator


T = TypeVar("T")


class Schema(BaseModel, Generic[T]):
    """A schema for (de)serializing data (JSON, YAML, etc.)"""

    version: str = "1.0.0"  # TODO: use harborapi.models.SemVer?
    type: Optional[str] = None  # should only be None if empty list
    module: Optional[str] = None
    data: Union[T, List[T]]

    class Config:
        extra = "allow"

    @classmethod
    def from_data(cls, data: T) -> Schema[T]:
        """Create a schema from data"""
        return cls(data=data)

    @classmethod
    def from_file(cls, path: Path) -> Schema:
        """Load a schema from a file"""
        if path.suffix == ".json":
            obj = cls.parse_file(path)
        else:
            raise ValueError(f"Unsupported file type {path.suffix}")
        return obj

    @root_validator
    def set_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # If schema has type and module, we are loading from a file
        if values.get("type") is not None and values.get("module") is not None:
            cls._parse_data(values)
            return values

        data = values.get("data")
        if isinstance(data, Sequence):
            if not data:
                return values
            data = data[0]

        typ = type(data)
        if typ is None:
            return values  # no validation to perform

        module = inspect.getmodule(typ)
        if not module:
            raise ValueError(f"Unknown data type: {typ}")

        # Determine the correct type name
        for n in [typ.__qualname__, typ.__name__]:
            try:
                typ = getattr(module, n)  # check if we can getattr the type
                values["type"] = n
                break
            except AttributeError:
                pass
        else:
            raise ValueError(f"Unknown data type: {typ}")

        values["module"] = module.__name__
        cls._parse_data(values)
        return values

    @classmethod
    def _parse_data(cls, values: Dict[str, Any]) -> None:
        """Parses the value of data into the correct type if possible."""
        module = importlib.import_module(values["module"])
        typ = getattr(module, values["type"])
        try:
            if issubclass(typ, BaseModel):
                values["data"] = typ.parse_obj(values["data"])
        except TypeError:
            pass
