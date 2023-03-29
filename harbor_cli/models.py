"""Models used by various modules.

Defined here to avoid circular imports when using these models in multiple
modules that otherwise can't mutually import each other.
Refactor to module (directory with __init__.py) if needed.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from typing import List
from typing import Optional

from click.core import Argument
from click.core import Parameter
from harborapi.models import Project
from harborapi.models.base import BaseModel as HarborAPIBaseModel
from typer.core import TyperArgument
from typer.core import TyperCommand

from .utils.utils import markup_as_plain_text


class BaseModel(HarborAPIBaseModel):
    pass


def get(param: Any, attr: str) -> Any:
    return getattr(param, attr, None)


class ParamSummary(BaseModel):
    """Serializable representation of a click.Parameter."""

    allow_from_autoenv: Optional[bool] = None
    confirmation_prompt: Optional[bool] = None
    choices: Optional[List[str]] = None
    count: Optional[bool] = None
    default: Optional[Any] = None
    envvar: Optional[str]
    expose_value: bool
    flag_value: Optional[Any] = None
    help: str
    hidden: Optional[bool] = None
    human_readable_name: str
    is_argument: bool
    is_bool_flag: Optional[bool] = None
    is_flag: Optional[bool] = None
    is_option: Optional[bool]
    max: Optional[int] = None
    min: Optional[int] = None
    metavar: Optional[str]
    multiple: bool
    name: str
    nargs: int
    prompt: Optional[str] = None
    prompt_required: Optional[bool] = None
    required: bool
    show_choices: Optional[bool] = None
    show_default: Optional[bool] = None
    show_envvar: Optional[bool] = None
    type: str
    value_from_envvar: Any

    @classmethod
    def from_param(cls, param: Parameter) -> ParamSummary:
        """Construct a new ParamSummary from a click.Parameter."""
        try:
            help_ = param.help or ""  # type: ignore
        except AttributeError:
            help_ = ""

        is_argument = isinstance(param, (Argument, TyperArgument))
        return cls(
            allow_from_autoenv=get(param, "allow_from_autoenv"),
            confirmation_prompt=get(param, "confirmation_prompt"),
            count=get(param, "count"),
            choices=get(param.type, "choices"),
            default=param.default,
            envvar=param.envvar,
            expose_value=param.expose_value,
            flag_value=get(param, "flag_value"),
            help=help_,
            hidden=get(param, "hidden"),
            human_readable_name=param.human_readable_name,
            is_argument=is_argument,
            is_bool_flag=get(param, "is_bool_flag"),
            is_eager=param.is_eager,
            is_flag=get(param, "is_flag"),
            is_option=get(param, "is_option"),
            max=get(param.type, "max"),
            min=get(param.type, "min"),
            metavar=param.metavar,
            multiple=param.multiple,
            name=param.name,
            nargs=param.nargs,
            opts=param.opts,
            prompt=get(param, "prompt"),
            prompt_required=get(param, "prompt_required"),
            required=param.required,
            secondary_opts=param.secondary_opts,
            show_choices=get(param, "show_choices"),
            show_default=get(param, "show_default"),
            show_envvar=get(param, "show_envvar"),
            type=param.type.name,
        )

    @property
    def help_plain(self) -> str:
        return markup_as_plain_text(self.help)


# TODO: split up CommandSummary into CommandSummary and CommandSearchResult
# so that the latter can have the score field
class CommandSummary(BaseModel):
    """Convenience class for accessing information about a command."""

    name: str
    category: Optional[str] = None
    help: str
    options_metavar: str
    score: int = 0  # match score
    params: List[ParamSummary] = []

    @classmethod
    def from_command(
        cls, command: TyperCommand, name: str | None = None, category: str | None = None
    ) -> CommandSummary:
        """Construct a new CommandSummary from a TyperCommand."""
        return cls(
            name=name or command.name or "",
            category=category,
            help=command.help or "",
            options_metavar=command.options_metavar or "",
            params=[ParamSummary.from_param(p) for p in command.params],
        )

    @property
    def help_plain(self) -> str:
        return markup_as_plain_text(self.help)

    @property
    def usage(self) -> str:
        # TODO: determine if we should show metavar or not
        # TODO: render required options!
        parts = [self.name]

        # Assume arg list is sorted by required/optional
        # Show required in angle brackets, optional in square brackets
        for arg in self.arguments:
            metavar = arg.metavar or arg.human_readable_name
            if arg.required:
                parts.append(f"<{metavar}>")
            else:
                parts.append(f"[{metavar}]")

        # Command with both required and optional options:
        # `command <required_option> [OPTIONS]`
        # Only required option(s):
        # `command <required_option> <required_option>`
        # Only optional options:
        # `command [OPTIONS]`
        has_optional = False
        for option in self.options:
            if option.required:
                parts.append(f"<{option.metavar or option.human_readable_name}>")
            else:
                has_optional = True
        else:
            if has_optional:
                parts.append("[OPTIONS]")

        return " ".join(parts)

    @property
    def options(self) -> List[ParamSummary]:
        return [p for p in self.params if not p.is_argument]

    @property
    def arguments(self) -> List[ParamSummary]:
        return [p for p in self.params if p.is_argument]


class ProjectExtended(Project):
    """Signal to the render function that we want to print extended information about a project."""

    pass


class Operator(Enum):
    """Operator used to detmerine matching of multiple search criteria."""

    AND = "and"
    OR = "or"
    XOR = "xor"


# We use this enum to provide choices in the CLI, but we also use it to determine
# the integer value of the group type when we need to send it to the API.
class UserGroupType(str, Enum):
    LDAP = "LDAP"
    HTTP = "HTTP"
    OIDC = "OIDC"

    @classmethod
    def from_int(cls, value: int) -> UserGroupType:
        try:
            return _USERGROUPTYPE_MAPPING[value]
        except KeyError:
            raise ValueError(f"Unknown user group type: {value}")

    def as_int(self) -> int:
        try:
            return _USERGROUPTYPE_MAPPING_REVERSE[self]
        except KeyError:
            raise ValueError(f"Unknown user group type: {self}")


# NOTE: could replace with a bidict or similar
_USERGROUPTYPE_MAPPING = {
    1: UserGroupType.LDAP,
    2: UserGroupType.HTTP,
    3: UserGroupType.OIDC,
}  # type: dict[int, UserGroupType]

_USERGROUPTYPE_MAPPING_REVERSE = {
    v: k for k, v in _USERGROUPTYPE_MAPPING.items()
}  # type: dict[UserGroupType, int]


# We use this enum to provide choices in the CLI, but we also use it to determine
# the integer value of the role when we need to send it to the API.
class MemberRoleType(Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    GUEST = "guest"
    MAINTAINER = "maintainer"

    @classmethod
    def from_int(cls, value: int) -> MemberRoleType:
        try:
            return _MEMBERROLETYPE_MAPPING[value]
        except KeyError:
            raise ValueError(f"Unknown role type: {value}")

    def as_int(self) -> int:
        try:
            return _MEMBERROLETYPE_MAPPING_REVERSE[self]
        except KeyError:
            raise ValueError(f"Unknown role type: {self}")


_MEMBERROLETYPE_MAPPING = {
    1: MemberRoleType.ADMIN,
    2: MemberRoleType.DEVELOPER,
    3: MemberRoleType.GUEST,
    4: MemberRoleType.MAINTAINER,
}  # type: dict[int, MemberRoleType]

_MEMBERROLETYPE_MAPPING_REVERSE = {
    v: k for k, v in _MEMBERROLETYPE_MAPPING.items()
}  # type: dict[MemberRoleType, int]
