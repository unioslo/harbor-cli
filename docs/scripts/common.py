from __future__ import annotations

from pathlib import Path

DOC_PATH = Path(__file__).parent.parent
DATA_PATH = DOC_PATH / "data"
if not DATA_PATH.exists():
    DATA_PATH.mkdir(parents=True)
