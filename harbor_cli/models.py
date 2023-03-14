"""Models used by various modules.

Defined here to avoid circular imports when using these models in multiple
modules that otherwise can't mutually import each other.
Refactor to module (directory with __init__.py) if needed.
"""
from __future__ import annotations

from enum import Enum

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


class Operator(Enum):
    """Operator used to detmerine matching of multiple search criteria."""

    AND = "and"
    OR = "or"
    XOR = "xor"


class UserGroupType(str, Enum):
    LDAP = "LDAP"
    HTTP = "HTTP"
    OIDC = "OIDC"

    @classmethod
    def from_int(cls, value: int) -> UserGroupType:
        if value == 1:
            return cls.LDAP
        elif value == 2:
            return cls.HTTP
        elif value == 3:
            return cls.OIDC
        else:
            raise ValueError(f"Unknown group type: {value}")

    def as_int(self) -> int:
        if self == UserGroupType.LDAP:
            return 1
        elif self == UserGroupType.HTTP:
            return 2
        elif self == UserGroupType.OIDC:
            return 3
        else:
            raise ValueError(f"Unknown group type: {self}")


class MemberRoleType(Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    GUEST = "guest"
    MAINTAINER = "maintainer"

    @classmethod
    def from_int(cls, value: int) -> MemberRoleType:
        if value == 1:
            return cls.ADMIN
        elif value == 2:
            return cls.DEVELOPER
        elif value == 3:
            return cls.GUEST
        elif value == 4:
            return cls.MAINTAINER
        else:
            raise ValueError(f"Unknown role type: {value}")

    def as_int(self) -> int:
        if self == MemberRoleType.ADMIN:
            return 1
        elif self == MemberRoleType.DEVELOPER:
            return 2
        elif self == MemberRoleType.GUEST:
            return 3
        elif self == MemberRoleType.MAINTAINER:
            return 4
        else:
            raise ValueError(f"Unknown role type: {self}")
