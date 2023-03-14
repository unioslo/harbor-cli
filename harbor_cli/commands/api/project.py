from __future__ import annotations

from typing import List
from typing import Optional

import typer
from harborapi.models.base import BaseModel
from harborapi.models.models import Project
from harborapi.models.models import ProjectMetadata
from harborapi.models.models import ProjectReq
from harborapi.models.models import RoleRequest

from ...logs import logger
from ...models import MemberRoleType
from ...models import ProjectExtended
from ...output.console import exit_err
from ...output.render import render_result
from ...state import state
from ...utils import parse_commalist
from ...utils.args import create_updated_model
from ...utils.args import get_ldap_group_arg
from ...utils.args import get_project_arg
from ...utils.args import get_user_arg
from ...utils.args import model_params_from_ctx
from ...utils.args import parse_key_value_args
from ...utils.commands import ARG_PROJECT_NAME
from ...utils.commands import inject_help
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE
from ...utils.commands import OPTION_PROJECT_ID
from ...utils.prompts import check_enumeration_options
from ...utils.prompts import delete_prompt

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
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    """Get information about a project."""
    arg = get_project_arg(project_name, project_id)
    project = get_project(arg)
    p = ProjectExtended(**project.dict())
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
    logger.info(f"Fetched {len(logs)} logs.")
    render_result(logs, ctx)


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
    raise SystemExit(0 if exists else 1)


class ProjectCreateResult(BaseModel):
    location: str
    project: ProjectReq


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
            public=public,
            enable_content_trust=enable_content_trust,
            enable_content_trust_cosign=enable_content_trust_cosign,
            prevent_vul=prevent_vul,
            severity=severity,
            auto_scan=auto_scan,
            reuse_sys_cve_allowlist=reuse_sys_cve_allowlist,
            retention_id=retention_id,
        ),
    )
    location = state.run(
        state.client.create_project(project_req), "Creating project..."
    )
    project_repr = get_project_repr(project_name)
    logger.info(f"Created {project_repr}")
    res = ProjectCreateResult(location=location, project=project_req)
    render_result(res, ctx)


# HarborAsyncClient.get_projects()
@app.command("list")
@inject_resource_options()
def list_projects(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page_size: int,
    limit: Optional[int],
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Name of a specific project to fetch.",
    ),
    public: Optional[bool] = typer.Option(
        None,
        help="Filter projects by whether they are public.",
    ),
    owner: Optional[str] = typer.Option(
        None,
        "--owner",
        help="Filter projects by the user who owns them.",
    ),
    with_detail: bool = typer.Option(
        True,
        help="Fetch detailed information about each project.",
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
            with_detail=with_detail,
            page_size=page_size,
            limit=limit,
        ),
        "Fetching projects...",
    )
    logger.info(f"Fetched {len(projects)} projects.")
    render_result(projects, ctx)


# HarborAsyncClient.update_project()
@app.command("update", no_args_is_help=True)
@inject_help(ProjectReq)
@inject_help(
    ProjectMetadata
)  # inject this first so its "public" field takes precedence
def update_project(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
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

    arg = get_project_arg(project_name, project_id)
    project = get_project(arg)
    if project.metadata is None:
        project.metadata = ProjectMetadata()

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
    logger.info(f"Updated {get_project_repr(arg)}")


# HarborAsyncClient.delete_project()
@app.command("delete")
def delete_project(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a project."""
    arg = get_project_arg(project_name, project_id)
    delete_prompt(config=state.config, force=force, resource="project", name=str(arg))
    project_repr = get_project_repr(arg)
    state.run(state.client.delete_project(arg), f"Deleting {project_repr}...")
    logger.info(f"Deleted {project_repr}.")


# HarborAsyncClient.get_project_summary()
@app.command("summary")
def get_project_summary(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    """Fetch project summary."""
    arg = get_project_arg(project_name, project_id)
    project_repr = get_project_repr(arg)
    summary = state.run(
        state.client.get_project_summary(arg), f"Fetching summary for {project_repr}..."
    )
    render_result(summary, ctx)


# HarborAsyncClient.get_project_scanner()
@scanner_cmd.command("get")
def get_project_scanner(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    arg = get_project_arg(project_name, project_id)
    scanner = state.run(state.client.get_project_scanner(arg))
    render_result(scanner, ctx)


# HarborAsyncClient.set_project_scanner()
@scanner_cmd.command("set")
def set_project_scanner(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
    scanner_id: str = typer.Argument(
        ...,
        help="ID of the scanner to set.",
    ),
) -> None:
    arg = get_project_arg(project_name, project_id)
    project_repr = get_project_repr(arg)
    scanner_repr = f"scanner with ID {scanner_id!r}"
    state.run(
        state.client.set_project_scanner(arg, scanner_id), f"Setting project scanner..."
    )
    logger.info(f"Set scanner for {project_repr} to {scanner_repr}")


# HarborAsyncClient.get_project_scanner_candidates()
@scanner_cmd.command("candidates")
@inject_resource_options
def get_project_scanner_candidates(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    arg = get_project_arg(project_name, project_id)
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
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    """Get metadata for a project."""
    arg = get_project_arg(project_name, project_id)
    metadata = state.run(state.client.get_project_metadata(arg), "Fetching metadata...")
    render_result(metadata, ctx)


# HarborAsyncClient.set_project_metadata()
@metadata_cmd.command("set", short_help="Set metadata for a project.")
@inject_help(ProjectMetadata)
def set_project_metadata(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
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
            "Extra metadata to set beyond the fields in the spec."
            "Format: [green]key[/green][magenta]=[/magenta][cyan]value[/cyan]. "
            "May be specified multiple times, or as a comma-separated list."
        ),
        metavar="KEY=VALUE",
        callback=parse_commalist,
    ),
) -> None:
    """Set metadata for a project. Until Harbor API spec"""
    # Model field args
    params = model_params_from_ctx(ctx, ProjectMetadata)

    # Extra metadata args
    extra_metadata = parse_key_value_args(extra)
    arg = get_project_arg(project_name, project_id)

    metadata = ProjectMetadata(
        **params,
        **extra_metadata,
    )

    project_repr = get_project_repr(arg)
    state.run(
        state.client.set_project_metadata(arg, metadata),
        f"Setting metadata for {project_repr}...",
    )
    logger.info(f"Set metadata for {project_repr}.")


# HarborAsyncClient.get_project_metadata_entry()
@metadata_field_cmd.command("get")
def get_project_metadata_field(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
    field: str = typer.Argument(
        ...,
        help="The name of the field to get.",
    ),
) -> None:
    """Get a single field from the metadata for a project. NOTE: does not support table output currently."""
    arg = get_project_arg(project_name, project_id)
    project_repr = get_project_repr(arg)
    metadata = state.run(
        state.client.get_project_metadata_entry(arg, field),
        f"Fetching metadata field {field!r} for {project_repr}...",
    )
    render_result(metadata, ctx)


# HarborAsyncClient.update_project_metadata_entry()
@metadata_field_cmd.command("set")
def set_project_metadata_field(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
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
    if field not in ProjectMetadata.__fields__:
        logger.warning(f"Field {field!r} is not a known project metadata field.")

    arg = get_project_arg(project_name, project_id)
    project_repr = get_project_repr(arg)

    metadata = ProjectMetadata.parse_obj({field: value})

    state.run(
        state.client.update_project_metadata_entry(arg, field, metadata),
        f"Setting metadata for {project_repr}...",
    )
    logger.info(f"Set metadata for {project_repr}.")


# HarborAsyncClient.delete_project_metadata_entry()
@metadata_field_cmd.command("delete")
def delete_project_metadata_field(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    project_id: Optional[int] = OPTION_PROJECT_ID,
    field: str = typer.Argument(
        ...,
        help="The metadata field to delete.",
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a single field in the metadata for a project."""
    delete_prompt(state.config, force, resource="metadata field", name=field)
    if field not in ProjectMetadata.__fields__:
        logger.warning(f"Field {field!r} is not a known project metadata field.")

    arg = get_project_arg(project_name, project_id)

    state.run(
        state.client.delete_project_metadata_entry(arg, field),
        f"Deleting metadata field {field!r}...",
    )
    logger.info(f"Deleted metadata field {field!r}.")


# HarborAsyncClient.get_project_member()
@member_cmd.command("get")
def get_project_member(
    ctx: typer.Context,
    project_name: Optional[str] = ARG_PROJECT_NAME,
    member_id: int = typer.Argument(..., help="The ID of the member to get."),
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    arg = get_project_arg(project_name, project_id)
    member = state.run(
        state.client.get_project_member(arg, member_id),
        f"Fetching member...",
    )
    render_result(member, ctx)


# HarborAsyncClient.add_project_member() # NYI


# HarborAsyncClient.add_project_member_user()
@member_cmd.command("add-user")
def add_project_member(
    ctx: typer.Context,
    # Required args
    project_name: Optional[str] = ARG_PROJECT_NAME,
    username: str = typer.Argument(..., help="The name of the user to add."),
    role: MemberRoleType = typer.Argument(
        ..., help="The type of role to give the user."
    ),
    # ID overrides options
    project_id: Optional[int] = OPTION_PROJECT_ID,
    user_id: Optional[int] = typer.Option(
        ..., help="The ID of the user to add. Overrides username."
    ),
) -> None:
    """Add a user as a member of a project."""
    project_arg = get_project_arg(project_name, project_id)
    user_arg = get_user_arg(username, user_id)
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
    project_name: Optional[str] = ARG_PROJECT_NAME,
    ldap_group_dn: str = typer.Argument(..., help="The name of the user to add."),
    role: MemberRoleType = typer.Argument(
        ..., help="The type of role to give the user."
    ),
    # ID overrides options
    project_id: Optional[int] = OPTION_PROJECT_ID,
    group_id: Optional[int] = typer.Option(
        ..., help="The ID of the user to add. Overrides username."
    ),
) -> None:
    """Add a user as a member of a project."""
    project_arg = get_project_arg(project_name, project_id)
    group_arg = get_ldap_group_arg(ldap_group_dn, group_id)
    member = state.run(
        state.client.add_project_member_group(project_arg, group_arg, role.as_int()),
        f"Adding group member...",
    )
    render_result(member, ctx)


# HarborAsyncClient.update_project_member_role()
@member_cmd.command("update-role")
def update_project_member_role(
    ctx: typer.Context,
    # Required args
    project_name: Optional[str] = ARG_PROJECT_NAME,
    member_id: int = typer.Argument(..., help="The ID of the member to update."),
    role: MemberRoleType = typer.Argument(
        ..., help="The type of role to give the user."
    ),
    # ID overrides options
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    """Add a user as a member of a project."""
    project_arg = get_project_arg(project_name, project_id)
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
    project_name: Optional[str] = ARG_PROJECT_NAME,
    member_id: int = typer.Argument(..., help="The ID of the member to remove."),
    # ID overrides options
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    project_arg = get_project_arg(project_name, project_id)
    state.run(
        state.client.remove_project_member(project_arg, member_id),
        f"Removing member...",
    )
    logger.info(f"Removed member {member_id} from project {project_arg}.")


# HarborAsyncClient.get_project_members()
@member_cmd.command("list")
@inject_resource_options()
def list_project_members(
    ctx: typer.Context,
    # Required args
    project_name: Optional[str] = ARG_PROJECT_NAME,
    # Optional args
    entity_name: Optional[str] = typer.Option(
        None, "--entity", help="Entity name to search for."
    ),
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
    # ID overrides options
    project_id: Optional[int] = OPTION_PROJECT_ID,
) -> None:
    """List all members of a project."""
    project_arg = get_project_arg(project_name, project_id)
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
