"""Somewhat experimental schema for (de)serializing data (JSON, YAML, etc.)

The aim is to be able to serialize a Pydantic model to JSON, YAML, etc. and
include metadata about the model in the serialized data. This metadata can
then be used to deserialize the data back into the correct Pydantic model.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any
from typing import Generic
from typing import TypeVar

from harborapi.models.base import BaseModel as HarborBaseModel
from pydantic import BaseModel
from pydantic import root_validator

from ..logs import logger

T = TypeVar("T")


class Schema(BaseModel, Generic[T]):
    """A schema for (de)serializing data (JSON, YAML, etc.)"""

    version: str = "1.0.0"
    data: T | list[T]
    type_: str | None = None
    is_list: bool = False

    @root_validator
    def set_type(cls, values: dict[str, Any]) -> dict[str, Any]:
        data = values.get("data")
        if isinstance(data, BaseModel):
            typ = data.__class__.__name__
        elif isinstance(data, list):  # JSON iterables are always list
            if all(isinstance(item, BaseModel) for item in data):
                typ = str(data[0].__class__.__name__)
            else:
                typ = str(type(data[0])) if data else None  # type: ignore
            values["is_list"] = True
        else:
            typ = str(type(data))
        values["type_"] = typ
        return values

    def update_data_type(self) -> Schema:
        """Re-validates the data using the type_ attribute.

        After deserializing, we need to re-validate the data using the
        type_ attribute. This is because the default data type for the
        data field is BaseModel | list[BaseModel], but we want to
        use the actual harborapi.models data type to get the correct
        field names and types, as well as any custom validation, methods
        and properties tied to the data type.
        """
        module = importlib.import_module("harborapi.models")
        if self.type_ is None:
            return self
        try:
            data_type = getattr(module, self.type_)
            assert issubclass(data_type, HarborBaseModel)
            if isinstance(self.data, list):
                for i, item in enumerate(self.data):
                    self.data[i] = data_type.parse_obj(item)
            else:
                self.data = data_type.parse_obj(self.data)
        except (ImportError, TypeError, AttributeError):
            logger.warning(
                f"Unable to import data type {self.type_} from harborapi.models"
            )
        # TODO: catch AssertionError?
        return self

    @classmethod
    def from_file(cls, path: Path) -> Schema:
        """Load a schema from a file"""
        if path.suffix == ".json":
            obj = cls.parse_file(path)
        else:
            raise ValueError(f"Unsupported file type {path.suffix}")
        # Update the data type after deserializing
        obj.update_data_type()
        return obj
