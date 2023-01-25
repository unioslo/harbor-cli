"""Models used by various modules.

Defined here to avoid circular imports when using these models in multiple
modules that otherwise can't mutually import each other.
Refactor to module (directory with __init__.py) if needed.
"""
from __future__ import annotations

from harborapi.models.base import BaseModel


class CommandSummary(BaseModel):
    name: str
    help: str
    score: int = 0  # match score
