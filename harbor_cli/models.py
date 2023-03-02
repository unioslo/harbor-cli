"""Models used by various modules.

Defined here to avoid circular imports when using these models in multiple
modules that otherwise can't mutually import each other.
Refactor to module (directory with __init__.py) if needed.
"""
from __future__ import annotations

from harborapi.models import Project
from harborapi.models.base import BaseModel as HarborAPIBaseModel


class BaseModel(HarborAPIBaseModel):
    pass


# TODO: split up CommandSummary into CommandSummary and CommandSearchResult
# so that the latter can have the score field
class CommandSummary(BaseModel):
    name: str
    help: str
    score: int = 0  # match score


class ProjectExtended(Project):
    """Signal to the render function that we want to print extended information about a project."""

    pass
