from __future__ import annotations

from typing import List
from typing import Optional

import typer
from harborapi.models.models import Project
from harborapi.models.models import ProjectMetadata
from harborapi.models.models import ProjectReq
from harborapi.models.models import RoleRequest

from ...models import MemberRoleType
from ...models import MetadataFields
from ...models import ProjectCreateResult
from ...models import ProjectExtended
from ...output.console import exit_err
from ...output.console import exit_ok
from ...output.console import info
from ...output.console import warning
from ...output.prompts import check_enumeration_options
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...state import get_state
from ...style.style import render_cli_value
from ...utils import parse_commalist
from ...utils.args import create_updated_model
from ...utils.args import get_ldap_group_arg
from ...utils.args import get_project_arg
from ...utils.args import get_user_arg
from ...utils.args import model_params_from_ctx
from ...utils.args import parse_key_value_args
from ...utils.commands import ARG_LDAP_GROUP_DN_OR_ID
from ...utils.commands import ARG_PROJECT_NAME_OR_ID
from ...utils.commands import ARG_USERNAME_OR_ID
from ...utils.commands import inject_help
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE

state = get_state()

# Create a command group
app = typer.Typer(
    name="project",
    help="Manage projects.",
    no_args_is_help=True,
)
scanner_cmd = typer.Typer(
    name="scanner",
    help="Manage project scanners.",
    no_args_is_help=True,
)
metadata_cmd = typer.Typer(
    name="metadata",
    help="Manage project metadata.",
    no_args_is_help=True,
)
metadata_field_cmd = typer.Typer(
    name="field",
    help="Manage project metadata fields.",
    no_args_is_help=True,
)
member_cmd = typer.Typer(
    name="member",
    help="Manage project members.",
    no_args_is_help=True,
)
metadata_cmd.add_typer(metadata_field_cmd)
app.add_typer(scanner_cmd)
app.add_typer(metadata_cmd)
app.add_typer(member_cmd)


def get_project(name_or_id: str | int) -> Project:
    return state.run(state.client.get_project(name_or_id), "Fetching project...")


# HarborAsyncClient.get_project()
@app.command("get", no_args_is_help=True)
def get_project_info(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
) -> None:
    """Get information about a project."""
    arg = get_project_arg(project_name_or_id)
    project = get_project(arg)
    p = ProjectExtended(**project.model_dump())
    render_result(p, ctx)


# HarborAsyncClient.get_project_logs()
@app.command("logs")
@inject_resource_options()
def get_project_logs(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    limit: Optional[int],
    project_name: str = typer.Argument(
        ...,
        help="Project name to fetch logs for.",
    ),
) -> None:
    """Fetch logs for a project."""
    check_enumeration_options(state, query=query, limit=limit)
    project_repr = get_project_repr(project_name)
    logs = state.run(
        state.client.get_project_logs(
            project_name,
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching logs for {project_repr}...",
    )
    render_result(logs, ctx)
    info(f"Fetched {len(logs)} logs.")


# HarborAsyncClient.project_exists()
@app.command(
    "exists",
    help="Check if a project with the given name exists.",
    no_args_is_help=True,
)
def project_exists(
    ctx: typer.Context,
    project_name: str = typer.Argument(..., help="Project name to check existence of."),
) -> None:
    """Check if a project exists."""
    project_repr = get_project_repr(project_name)
    exists = state.run(
        state.client.project_exists(project_name),
        f"Checking if {project_repr} exists...",
    )
    render_result(exists, ctx)
    exit_ok(code=0 if exists else 1)


# HarborAsyncClient.create_project()
@app.command("create", no_args_is_help=True)
@inject_help(ProjectReq)
@inject_help(
    ProjectMetadata
)  # inject this first so its "public" field takes precedence
def create_project(
    ctx: typer.Context,
    project_name: str = typer.Argument(
        ...,
    ),
    storage_limit: Optional[int] = typer.Option(
        None,
        "--storage-limit",
    ),
    registry_id: Optional[int] = typer.Option(
        None,
        "--registry-id",
    ),
    # Options from the Metadata model
    public: Optional[bool] = typer.Option(
        None,
        "--public",
        is_flag=False,
    ),
    enable_content_trust: Optional[bool] = typer.Option(
        None,
        "--content-trust",
        is_flag=False,
    ),
    enable_content_trust_cosign: Optional[bool] = typer.Option(
        None,
        "--content-trust-cosign",
        is_flag=False,
    ),
    prevent_vul: Optional[bool] = typer.Option(
        None,
        "--prevent-vul",
        is_flag=False,
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        # TODO: add custom help text? The original help text has some really broken English...
    ),
    auto_scan: Optional[bool] = typer.Option(
        None,
        "--auto-scan",
        is_flag=False,
    ),
    reuse_sys_cve_allowlist: Optional[bool] = typer.Option(
        None,
        "--reuse-sys-cve-allowlist",
        is_flag=False,
    ),
    retention_id: Optional[str] = typer.Option(
        None,
        "--retention-id",
    ),
    # TODO: add support for adding CVE allowlist when creating a project
) -> None:
    """Create a new project."""
    project_req = ProjectReq(
        project_name=project_name,
        storage_limit=storage_limit,
        registry_id=registry_id,
        metadata=ProjectMetadata(
            # validator does bool -> str conversion for the string bool fields
            public=public,  # type: ignore
            enable_content_trust=enable_content_trust,  # type: ignore
            enable_content_trust_cosign=enable_content_trust_cosign,  # type: ignore
            prevent_vul=prevent_vul,  # type: ignore
            severity=severity,
            auto_scan=auto_scan,  # type: ignore
            reuse_sys_cve_allowlist=reuse_sys_cve_allowlist,  # type: ignore
            retention_id=retention_id,
        ),
    )
    location = state.run(
        state.client.create_project(project_req), "Creating project..."
    )
    project_repr = get_project_repr(project_name)
    info(f"Created {project_repr}")
    res = ProjectCreateResult(location=location, project=project_req)
    render_result(res, ctx)


# HarborAsyncClient.get_projects()
@app.command("list")
@inject_resource_options()
def list_projects(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str] = typer.Option(
        "name",
        "--sort",
        help=(
            "Sort projects by the given field(s). "
            "Sortable fields: "
            f"{render_cli_value('name')}, "
            f"{render_cli_value('project_id')}, "
            f"{render_cli_value('creation_time')}"
        ),
    ),
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Name of a specific project to fetch.",
        hidden=True,
    ),
    public: Optional[bool] = typer.Option(
        None,
        "--public/--no-public",
        help="Filter projects by the given public status.",
    ),
    owner: Optional[str] = typer.Option(
        None,
        "--owner",
        help="Filter projects by the user who owns them.",
    ),
) -> None:
    """Fetch projects."""
    projects = state.run(
        state.client.get_projects(
            query=query,
            sort=sort,
            name=name,
            public=public,
            owner=owner,
            with_detail=True,
            page_size=page_size,
            limit=limit,
        ),
        "Fetching projects...",
    )
    render_result(projects, ctx)
    info(f"Fetched {len(projects)} projects.")


# HarborAsyncClient.update_project()
@app.command("update", no_args_is_help=True)
@inject_help(ProjectReq)
@inject_help(
    ProjectMetadata
)  # inject this first so its "public" field takes precedence
def update_project(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    storage_limit: Optional[int] = typer.Option(
        None,
        "--storage-limit",
    ),
    registry_id: Optional[int] = typer.Option(
        None,
        "--registry-id",
    ),
    # Options from the Metadata model
    public: Optional[bool] = typer.Option(
        None,
        "--public",
        is_flag=False,
    ),
    enable_content_trust: Optional[bool] = typer.Option(
        None,
        "--content-trust",
        is_flag=False,
    ),
    enable_content_trust_cosign: Optional[bool] = typer.Option(
        None,
        "--content-trust-cosign",
        is_flag=False,
    ),
    prevent_vul: Optional[bool] = typer.Option(
        None,
        "--prevent-vul",
        is_flag=False,
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        # TODO: add custom help text? The original help text has some really broken English...
    ),
    auto_scan: Optional[bool] = typer.Option(
        None,
        "--auto-scan",
        is_flag=False,
    ),
    reuse_sys_cve_allowlist: Optional[bool] = typer.Option(
        None,
        "--reuse-sys-cve-allowlist",
        is_flag=False,
    ),
    retention_id: Optional[str] = typer.Option(
        None,
        "--retention-id",
    ),
) -> None:
    """Update project information."""
    req_params = model_params_from_ctx(ctx, ProjectReq)
    metadata_params = model_params_from_ctx(ctx, ProjectMetadata)
    if not req_params and not metadata_params:
        exit_err("No parameters provided.")

    arg = get_project_arg(project_name_or_id)
    project = get_project(arg)
    if project.metadata is None:
        project.metadata = ProjectMetadata()  # type: ignore[call-arg] # mypy bug

    # Create updated models from params
    req = create_updated_model(
        project,
        ProjectReq,
        ctx,
        empty_ok=True,
    )
    metadata = create_updated_model(
        project.metadata,
        ProjectMetadata,
        ctx,
        empty_ok=True,
    )
    req.metadata = metadata

    state.run(state.client.update_project(arg, req), f"Updating project...")
    info(f"Updated {get_project_repr(arg)}")


# HarborAsyncClient.delete_project()
@app.command("delete")
def delete_project(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a project."""
    arg = get_project_arg(project_name_or_id)
    delete_prompt(config=state.config, force=force, resource="project", name=str(arg))
    project_repr = get_project_repr(arg)
    state.run(state.client.delete_project(arg), f"Deleting {project_repr}...")
    info(f"Deleted {project_repr}.")


# HarborAsyncClient.get_project_summary()
@app.command("summary")
def get_project_summary(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
) -> None:
    """Fetch project summary."""
    arg = get_project_arg(project_name_or_id)
    project_repr = get_project_repr(arg)
    summary = state.run(
        state.client.get_project_summary(arg), f"Fetching summary for {project_repr}..."
    )
    render_result(summary, ctx, project_name=project_name_or_id)


# HarborAsyncClient.get_project_scanner()
@scanner_cmd.command("get")
def get_project_scanner(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
) -> None:
    arg = get_project_arg(project_name_or_id)
    scanner = state.run(state.client.get_project_scanner(arg))
    render_result(scanner, ctx)


# HarborAsyncClient.set_project_scanner()
@scanner_cmd.command("set")
def set_project_scanner(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    scanner_id: str = typer.Argument(
        ...,
        help="ID of the scanner to set.",
    ),
) -> None:
    arg = get_project_arg(project_name_or_id)
    project_repr = get_project_repr(arg)
    scanner_repr = f"scanner with ID {scanner_id!r}"
    state.run(
        state.client.set_project_scanner(arg, scanner_id), f"Setting project scanner..."
    )
    info(f"Set scanner for {project_repr} to {scanner_repr}")


# HarborAsyncClient.get_project_scanner_candidates()
@scanner_cmd.command("candidates")
@inject_resource_options
def get_project_scanner_candidates(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
) -> None:
    arg = get_project_arg(project_name_or_id)
    project_repr = get_project_repr(arg)
    candidates = state.run(
        state.client.get_project_scanner_candidates(
            arg,
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
        ),
        f"Fetching scanner candidates for {project_repr}...",
    )
    render_result(candidates, ctx)


def get_project_repr(arg: str | int) -> str:
    """Get a human-readable representation of a project argument."""
    if isinstance(arg, str):
        return f"project {arg!r}"
    else:
        return f"project (id={arg})"


# Metadata commands (which are in their own category in Harbor API)


# HarborAsyncClient.get_project_metadata()
@metadata_cmd.command("get")
def get_project_metadata(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
) -> None:
    """Get metadata for a project."""
    arg = get_project_arg(project_name_or_id)
    metadata = state.run(state.client.get_project_metadata(arg), "Fetching metadata...")
    render_result(metadata, ctx)


# HarborAsyncClient.set_project_metadata()
@metadata_cmd.command("set")
@inject_help(ProjectMetadata)
def set_project_metadata(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    public: Optional[bool] = typer.Option(
        None,
        "--public",
        is_flag=False,
    ),
    enable_content_trust: Optional[bool] = typer.Option(
        None,
        "--content-trust",
        is_flag=False,
    ),
    content_trust_cosign: Optional[bool] = typer.Option(
        None,
        "--content-trust-cosign",
        is_flag=False,
    ),
    prevent_vul: Optional[bool] = typer.Option(
        None,
        "--prevent-vul",
        is_flag=False,
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
    ),
    auto_scan: Optional[bool] = typer.Option(
        None,
        "--auto-scan",
        is_flag=False,
    ),
    reuse_sys_cve_allowlist: Optional[bool] = typer.Option(
        None,
        "--reuse-sys-cve-allowlist",
        is_flag=False,
    ),
    retention_id: Optional[int] = typer.Option(
        None,
        "--retention-id",
    ),
    extra: List[str] = typer.Option(
        [],
        "--extra",
        help=(
            "Extra metadata to set beyond the fields in the spec. "
            f"Format: {render_cli_value('key=value')}. "
        ),
        metavar="KEY=VALUE",
        callback=parse_commalist,
    ),
) -> None:
    """Set metadata for a project."""
    # Model field args
    params = model_params_from_ctx(ctx, ProjectMetadata)

    # Extra metadata args
    extra_metadata = parse_key_value_args(extra)
    arg = get_project_arg(project_name_or_id)

    metadata = ProjectMetadata(
        **params,
        **extra_metadata,
    )

    project_repr = get_project_repr(arg)
    state.run(
        state.client.set_project_metadata(arg, metadata),
        f"Setting metadata for {project_repr}...",
    )
    info(f"Set metadata for {project_repr}.")


# HarborAsyncClient.get_project_metadata_entry()
@metadata_field_cmd.command("get")
def get_project_metadata_field(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    field: str = typer.Argument(
        ...,
        help="The name of the field to get.",
    ),
) -> None:
    """Get a single field from the metadata for a project. NOTE: does not support table output currently."""
    arg = get_project_arg(project_name_or_id)
    project_repr = get_project_repr(arg)
    metadata = state.run(
        state.client.get_project_metadata_entry(arg, field),
        f"Fetching metadata field {field!r} for {project_repr}...",
    )
    md = MetadataFields.model_validate(metadata)
    render_result(md, ctx)


# HarborAsyncClient.update_project_metadata_entry()
@metadata_field_cmd.command("set")
def set_project_metadata_field(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    field: str = typer.Argument(
        ...,
        help="The name of the field to set.",
    ),
    value: str = typer.Argument(
        ...,
        help="The value to set.",
    ),
) -> None:
    """Set a single field in the metadata for a project."""
    if field not in ProjectMetadata.model_fields:
        warning(f"Field {field!r} is not a known project metadata field.")

    arg = get_project_arg(project_name_or_id)
    project_repr = get_project_repr(arg)

    metadata = ProjectMetadata.model_validate({field: value})

    state.run(
        state.client.update_project_metadata_entry(arg, field, metadata),
        f"Setting metadata for {project_repr}...",
    )
    info(f"Set metadata for {project_repr}.")


# HarborAsyncClient.delete_project_metadata_entry()
@metadata_field_cmd.command("delete")
def delete_project_metadata_field(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    field: str = typer.Argument(
        ...,
        help="The metadata field to delete.",
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a single field in the metadata for a project."""
    delete_prompt(state.config, force, resource="metadata field", name=field)
    if field not in ProjectMetadata.model_fields:
        warning(f"Field {field!r} is not a known project metadata field.")

    arg = get_project_arg(project_name_or_id)

    state.run(
        state.client.delete_project_metadata_entry(arg, field),
        f"Deleting metadata field {field!r}...",
    )
    info(f"Deleted metadata field {field!r}.")


# HarborAsyncClient.get_project_member()
@member_cmd.command("get")
def get_project_member(
    ctx: typer.Context,
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    member_id: int = typer.Argument(..., help="The ID of the member to get."),
) -> None:
    arg = get_project_arg(project_name_or_id)
    member = state.run(
        state.client.get_project_member(arg, member_id),
        f"Fetching member...",
    )
    render_result(member, ctx)


# HarborAsyncClient.add_project_member() # NYI (probably no point?)


# HarborAsyncClient.add_project_member_user()
@member_cmd.command("add-user")
def add_project_member(
    ctx: typer.Context,
    # Required args
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    username_or_id: str = ARG_USERNAME_OR_ID,
    role: MemberRoleType = typer.Argument(
        ..., help="The type of role to give the user."
    ),
) -> None:
    """Add a user as a member of a project."""
    project_arg = get_project_arg(project_name_or_id)
    user_arg = get_user_arg(username_or_id)
    member = state.run(
        state.client.add_project_member_user(project_arg, user_arg, role.as_int()),
        f"Adding user member...",
    )
    render_result(member, ctx)


# HarborAsyncClient.add_project_member_group()
@member_cmd.command("add-group")
def add_project_member_group(
    ctx: typer.Context,
    # Required args
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    ldap_group_dn_or_id: str = ARG_LDAP_GROUP_DN_OR_ID,
    role: MemberRoleType = typer.Argument(
        ..., help="The type of role to give the user."
    ),
) -> None:
    """Add a group as a member of a project."""
    project_arg = get_project_arg(project_name_or_id)
    group_arg = get_ldap_group_arg(ldap_group_dn_or_id)
    member = state.run(
        state.client.add_project_member_group(project_arg, group_arg, role.as_int()),
        f"Adding group member...",
    )
    render_result(member, ctx)


def project_member_id_from_username_or_id(
    project_arg: str | int, username_or_id: str
) -> int:
    """Get a project member ID from a username or ID."""
    members = state.run(
        state.client.get_project_members(project_arg),
    )
    for member in members:
        if (
            member.id is not None
            and member.entity_type == "u"
            and (
                member.entity_name == username_or_id
                or member.entity_id == username_or_id
            )
        ):
            return member.id
    exit_err(f"Could not find member with username or ID {username_or_id!r}.")


# HarborAsyncClient.update_project_member_role()
@member_cmd.command("update-role")
def update_project_member_role(
    ctx: typer.Context,
    # Required args
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    username_or_id: str = ARG_USERNAME_OR_ID,
    role: MemberRoleType = typer.Argument(
        ..., help="The type of role to give the user."
    ),
) -> None:
    """Add a user as a member of a project."""
    project_arg = get_project_arg(project_name_or_id)
    member_id = project_member_id_from_username_or_id(project_arg, username_or_id)
    member = state.run(
        state.client.update_project_member_role(
            project_arg, member_id, RoleRequest(role_id=role.as_int())
        ),
        f"Updating member role...",
    )
    render_result(member, ctx)


# HarborAsyncClient.remove_project_member()
@member_cmd.command("remove")
def remove_project_member(
    ctx: typer.Context,
    # Required args
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    username_or_id: str = ARG_USERNAME_OR_ID,
) -> None:
    project_arg = get_project_arg(project_name_or_id)
    member_id = project_member_id_from_username_or_id(project_arg, username_or_id)
    state.run(
        state.client.remove_project_member(project_arg, member_id),
        f"Removing member...",
    )
    info(f"Removed member {member_id} from project {project_arg}.")


# HarborAsyncClient.get_project_members()
@member_cmd.command("list")
@inject_resource_options()
def list_project_members(
    ctx: typer.Context,
    # Required args
    project_name_or_id: str = ARG_PROJECT_NAME_OR_ID,
    # Optional args
    entity_name: Optional[str] = typer.Option(
        None, "--entity", help="Entity name to search for."
    ),
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
) -> None:
    """List all members of a project."""
    project_arg = get_project_arg(project_name_or_id)
    members = state.run(
        state.client.get_project_members(
            project_arg,
            entity_name=entity_name,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching members...",
    )
    render_result(members, ctx)
