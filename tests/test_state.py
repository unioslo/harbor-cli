from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from harbor_cli.state import State


def test_state_run_nohandle(state: State) -> None:
    async def coro() -> int:
        raise ValueError("test")

    # Single error type
    with pytest.raises(ValueError):
        state.run(coro(), no_handle=ValueError)

    # Tuple of error types
    with pytest.raises(ValueError):
        state.run(coro(), no_handle=(ValueError, TypeError))
