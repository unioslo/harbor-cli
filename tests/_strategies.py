from __future__ import annotations

import logging
import typing
import warnings
from typing import TYPE_CHECKING

from hypothesis import strategies as st
from pydantic import ValidationError

if TYPE_CHECKING:
    from pydantic import BaseModel  # noqa: F401
    from hypothesis.strategies import SearchStrategy  # noqa: F401

from harbor_cli.output.table import RENDER_FUNCTIONS


COMPACT_TABLE_MODELS = []  # type: list[SearchStrategy[BaseModel | list[BaseModel]]]
for model in RENDER_FUNCTIONS.keys():
    try:
        args = typing.get_args(model)
        strategy = st.lists(st.builds((args[0])), min_size=1)
    except (TypeError, IndexError):
        strategy = st.builds(model)
    # Ensure strategy is valid:
    # RootModel models such as harborapi.models.ExtraAttrs have been
    # observed to not generate valid strategies.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            strategy.example()
    except (ValidationError, TypeError):
        logging.warning(f"Skipping {model} for table rendering tests.")
        continue
    COMPACT_TABLE_MODELS.append(strategy)
    if not COMPACT_TABLE_MODELS:
        raise RuntimeError("No valid models found for table rendering tests.")
