from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from hypothesis import strategies as st

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
    COMPACT_TABLE_MODELS.append(strategy)
