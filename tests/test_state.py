from __future__ import annotations

import pytest

from harbor_cli.state import state


def test_state_run_nohandle() -> None:
    async def coro() -> int:
        raise ValueError("test")

    # Single error type
    with pytest.raises(ValueError):
        state.run(coro(), no_handle=ValueError)

    # Tuple of error types
    with pytest.raises(ValueError):
        state.run(coro(), no_handle=(ValueError, TypeError))
