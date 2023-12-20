"""Models used by various modules.

Defined here to avoid circular imports when using these models in multiple
modules that otherwise can't mutually import each other.
Refactor to module (directory with __init__.py) if needed.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional

from click.core import Argument
from click.core import Parameter
from harborapi.ext.artifact import ArtifactInfo
from harborapi.models import NativeReportSummary
from harborapi.models import Project
from harborapi.models import ProjectReq
from harborapi.models.base import BaseModel as HarborAPIBaseModel
from pydantic import Field
from pydantic import model_validator
from pydantic import RootModel
from rich.table import Table
from strenum import StrEnum
from typer.core import TyperArgument
from typer.core import TyperCommand

from .style.markup import markup_as_plain_text
from .style.markup import markup_to_markdown


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
    is_eager: bool = False
    is_bool_flag: Optional[bool] = None
    is_flag: Optional[bool] = None
    is_option: Optional[bool]
    max: Optional[int] = None
    min: Optional[int] = None
    metavar: Optional[str]
    multiple: bool
    name: Optional[str]
    nargs: int
    opts: List[str]
    prompt: Optional[str] = None
    prompt_required: Optional[bool] = None
    required: bool
    secondary_opts: List[str] = []
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
            envvar=param.envvar,  # TODO: support list of envvars
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
            value_from_envvar=param.value_from_envvar,
        )

    @property
    def help_plain(self) -> str:
        return markup_as_plain_text(self.help)

    @property
    def help_md(self) -> str:
        return markup_to_markdown(self.help)

    @model_validator(mode="before")
    def _fmt_metavar(cls, data: dict[str, Any]) -> dict[str, Any]:
        metavar = data.get("metavar") or data.get("human_readable_name", "")
        assert isinstance(metavar, str)
        metavar = metavar.upper()
        if data.get("multiple"):
            new_metavar = f"<{metavar},[{metavar}...]>"
        else:
            new_metavar = f"<{metavar}>"
        data["metavar"] = new_metavar
        return data


# TODO: split up CommandSummary into CommandSummary and CommandSearchResult
# so that the latter can have the score field
class CommandSummary(BaseModel):
    """Convenience class for accessing information about a command."""

    category: Optional[str] = None  # not part of TyperCommand
    deprecated: bool
    epilog: Optional[str]
    help: str
    hidden: bool
    name: str
    options_metavar: str
    params: List[ParamSummary] = []
    score: int = 0  # match score (not part of TyperCommand)
    short_help: Optional[str]

    @classmethod
    def from_command(
        cls, command: TyperCommand, name: str | None = None, category: str | None = None
    ) -> CommandSummary:
        """Construct a new CommandSummary from a TyperCommand."""
        return cls(
            category=category,
            deprecated=command.deprecated,
            epilog=command.epilog or "",
            help=command.help or "",
            hidden=command.hidden,
            name=name or command.name or "",
            options_metavar=command.options_metavar or "",
            params=[ParamSummary.from_param(p) for p in command.params],
            short_help=command.short_help or "",
        )

    @property
    def help_plain(self) -> str:
        return markup_as_plain_text(self.help)

    @property
    def help_md(self) -> str:
        return markup_to_markdown(self.help)

    @property
    def usage(self) -> str:
        parts = [self.name]

        # Assume arg list is sorted by required/optional
        # `<POSITIONAL_ARG1> <POSITIONAL_ARG2> [OPTIONAL_ARG1] [OPTIONAL_ARG2]`
        for arg in self.arguments:
            metavar = arg.metavar or arg.human_readable_name
            parts.append(metavar)

        # Command with both required and optional options:
        # `--option1 <opt1> --option2 <opt2> [OPTIONS]`
        has_optional = False
        for option in self.options:
            if option.required:
                metavar = option.metavar or option.human_readable_name
                if option.opts:
                    s = f"{max(option.opts)} {metavar}"
                else:
                    # this shouldn't happen, but just in case. A required
                    # option without any opts is not very useful.
                    # NOTE: could raise exception here instead
                    s = metavar
                parts.append(s)
            else:
                has_optional = True
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
class UserGroupType(StrEnum):
    LDAP = "LDAP"
    HTTP = "HTTP"
    OIDC = "OIDC"

    @classmethod
    def from_int(cls, value: int) -> str:
        try:
            return _USERGROUPTYPE_MAPPING[value]
        except KeyError:
            raise ValueError(f"Invalid user group type: {value}")

    def as_int(self) -> int:
        try:
            return _USERGROUPTYPE_MAPPING_REVERSE[self]
        except KeyError:
            raise ValueError(f"Unknown user group type: {self}")


# NOTE: Dict keys are typed as str instead of UserGroupType
# https://github.com/python/mypy/issues/14688


# NOTE: could replace with a bidict or similar
_USERGROUPTYPE_MAPPING = {
    1: UserGroupType.LDAP,
    2: UserGroupType.HTTP,
    3: UserGroupType.OIDC,
}  # type: dict[int, str]

_USERGROUPTYPE_MAPPING_REVERSE = {
    v: k for k, v in _USERGROUPTYPE_MAPPING.items()
}  # type: dict[str, int]


# We use this enum to provide choices in the CLI, but we also use it to determine
# the integer value of the role when we need to send it to the API.
class MemberRoleType(Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    GUEST = "guest"
    MAINTAINER = "maintainer"
    LIMITED_GUEST = "limited_guest"

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


# NOTE: I have no idea how I managed to determine these integer values.
# They do seem correct though, but I'd love to know how I got them, because
# to add a new role type, we need to manually test it out in the Web UI
# and inspect the request payload to see what integer value it sends.
_MEMBERROLETYPE_MAPPING = {
    1: MemberRoleType.ADMIN,
    2: MemberRoleType.DEVELOPER,
    3: MemberRoleType.GUEST,
    4: MemberRoleType.MAINTAINER,
    5: MemberRoleType.LIMITED_GUEST,
}  # type: dict[int, MemberRoleType]

_MEMBERROLETYPE_MAPPING_REVERSE = {
    v: k for k, v in _MEMBERROLETYPE_MAPPING.items()
}  # type: dict[MemberRoleType, int]


class ArtifactVulnerabilitySummary(BaseModel):
    artifact: str
    tags: List[str]
    summary: Optional[NativeReportSummary]
    # Not a property since we don't keep the original artifact around
    artifact_short: str = Field(..., exclude=True)

    @classmethod
    def from_artifactinfo(cls, artifact: ArtifactInfo) -> ArtifactVulnerabilitySummary:
        return cls(
            artifact=artifact.name_with_digest_full,
            artifact_short=artifact.name_with_digest,
            tags=artifact.tags,
            summary=artifact.artifact.scan,
        )


class MetadataFields(RootModel):
    """Renders a mapping of one or more metadata fields as a table."""

    root: Dict[str, Any]

    def as_table(self, **kwargs: Any) -> Iterable[Table]:  # type: ignore
        from .output.table._utils import get_table

        table = get_table(
            "Metadata Field",
            columns=["Field", "Value"],
            data=list(self.root),
        )
        for k, v in self.root.items():
            table.add_row(k, str(v))
        yield table


class ProjectCreateResult(BaseModel):
    location: str
    project: ProjectReq
