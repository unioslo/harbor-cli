from __future__ import annotations

from pathlib import Path

from harbor_cli.output.formatting.path import path_link


def test_path_link_absolute() -> None:
    """Test path_link with absolute=True."""
    p = Path("/tmp").resolve().absolute()
    assert path_link(p, absolute=True) == f"[link=file://{str(p)}]{str(p)}[/link]"


def test_path_link_relative() -> None:
    """Test path_link with absolute=False."""
    p = Path("/tmp")
    assert (
        path_link(p, absolute=False)
        == f"[link=file://{str(p.resolve().absolute())}]/tmp[/link]"
    )
