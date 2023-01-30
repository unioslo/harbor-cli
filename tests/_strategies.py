from __future__ import annotations

from typing import TYPE_CHECKING

from hypothesis import strategies as st

if TYPE_CHECKING:
    from pydantic import BaseModel  # noqa: F401
    from hypothesis.strategies import SearchStrategy  # noqa: F401

from harbor_cli.output.table import RENDER_FUNCTIONS


COMPACT_TABLE_MODELS = st.one_of(
    [st.builds(model) for model in RENDER_FUNCTIONS.keys()]
)  # type: SearchStrategy[BaseModel]
