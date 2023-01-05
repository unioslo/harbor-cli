from __future__ import annotations

from typing import List
from typing import Literal
from typing import Optional
from typing import overload

import typer
from harborapi.models.models import ProjectMetadata
from harborapi.models.models import ProjectReq

from ...logs import logger
from ...output.render import render_result
from ...state import state
from ...utils import inject_help
from ...utils import inject_resource_options
from ...utils import parse_commalist
from ...utils import parse_key_value_args
from ...utils.args import model_params_from_ctx

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
metadata_cmd.add_typer(metadata_field_cmd)
app.add_typer(scanner_cmd)
app.add_typer(metadata_cmd)

# HarborAsyncClient.get_project()
@app.command("get", no_args_is_help=True)
def get_project_info(
    ctx: typer.Context,
    project_name_or_id: str = typer.Argument(
        ...,
        help="Project name or ID to fetch info for. Numeric strings are interpreted as IDs.",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the project name is an ID.",
    ),
) -> None:
    """Get information about a project."""
    arg = get_project_arg(project_name_or_id, is_id)
    project_repr = get_project_repr(arg)
    project_info = state.run(
        state.client.get_project(arg), f"Fetching project info for {project_repr}..."
    )
    render_result(project_info, ctx)


# HarborAsyncClient.get_project_logs()
@app.command("logs")
@inject_resource_options()
def get_project_logs(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page: int,
    page_size: int,
    retrieve_all: bool,
    project_name: str = typer.Argument(
        ...,
        help="Project name to fetch logs for.",
    ),
) -> None:
    """Fetch recent logs for a project."""
    project_repr = get_project_repr(project_name)
    logs = state.run(
        state.client.get_project_logs(
            project_name,
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            retrieve_all=retrieve_all,
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
    """Check if a project exists. Exits with return code 0 if it does, 1 if it doesn't."""
    project_repr = get_project_repr(project_name)
    exists = state.run(
        state.client.project_exists(project_name),
        f"Checking if {project_repr} exists...",
    )
    logger.info(f"{project_name!r} exists: {exists}")
    render_result(exists, ctx)
    exit(0 if exists else 1)


# HarborAsyncClient.create_project()
@app.command("create")
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
    public: Optional[str] = typer.Option(
        None,
        "--public",
    ),
    enable_content_trust: Optional[str] = typer.Option(
        None,
        "--enable-content-trust",
    ),
    enable_content_trust_cosign: Optional[str] = typer.Option(
        None,
        "--enable-content-trust-cosign",
    ),
    prevent_vul: Optional[str] = typer.Option(
        None,
        "--prevent-vul",
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        # TODO: add custom help text? The original help text has some really broken English...
    ),
    auto_scan: Optional[str] = typer.Option(
        None,
        "--auto-scan",
    ),
    reuse_sys_cve_whitelist: Optional[str] = typer.Option(
        None,
        "--reuse-sys-cve-whitelist",
    ),
    retention_id: Optional[str] = typer.Option(
        None,
        "--retention-id",
    ),
    # TODO: add support for adding CVE allowlist when creating a project
) -> None:
    # TODO: allow passing 0 and 1, as well as "True" and "False" in addition to
    # "true" and "false" for fields in the models that accept "true" and "false",
    # but are str rather than bool (WHY, HARBOR?!)
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
            reuse_sys_cve_whitelist=reuse_sys_cve_whitelist,
            retention_id=retention_id,
        ),
    )
    project = state.run(state.client.create_project(project_req), "Creating project...")
    logger.info(f"Created project {project_name}")
    render_result(project, ctx)


# HarborAsyncClient.get_projects()
@app.command("list")
@inject_resource_options()
def list_projects(
    ctx: typer.Context,
    query: Optional[str],
    sort: Optional[str],
    page_size: int,
    retrieve_all: bool = typer.Option(
        True,
    ),
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
            retrieve_all=retrieve_all,
        ),
        "Fetching projects...",
    )
    logger.info(f"Fetched {len(projects)} projects.")
    render_result(projects, ctx)


# HarborAsyncClient.update_project()
@app.command("update", help="Update project information", no_args_is_help=True)
@inject_help(ProjectReq)
@inject_help(
    ProjectMetadata
)  # inject this first so its "public" field takes precedence
def update_project(
    ctx: typer.Context,
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to delete (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the project name is an ID.",
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
    public: Optional[str] = typer.Option(
        None,
        "--public",
    ),
    enable_content_trust: Optional[str] = typer.Option(
        None,
        "--enable-content-trust",
    ),
    enable_content_trust_cosign: Optional[str] = typer.Option(
        None,
        "--enable-content-trust-cosign",
    ),
    prevent_vul: Optional[str] = typer.Option(
        None,
        "--prevent-vul",
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        # TODO: add custom help text? The original help text has some really broken English...
    ),
    auto_scan: Optional[str] = typer.Option(
        None,
        "--auto-scan",
    ),
    reuse_sys_cve_whitelist: Optional[str] = typer.Option(
        None,
        "--reuse-sys-cve-whitelist",
    ),
    retention_id: Optional[str] = typer.Option(
        None,
        "--retention-id",
    ),
) -> None:
    arg = get_project_arg(project_name_or_id, is_id)
    project_repr = get_project_repr(arg)
    project_req = ProjectReq(
        project_name=arg if isinstance(arg, str) else None,
        storage_limit=storage_limit,
        registry_id=registry_id,
        metadata=ProjectMetadata(
            public=public,
            enable_content_trust=enable_content_trust,
            enable_content_trust_cosign=enable_content_trust_cosign,
            prevent_vul=prevent_vul,
            severity=severity,
            auto_scan=auto_scan,
            reuse_sys_cve_whitelist=reuse_sys_cve_whitelist,
            retention_id=retention_id,
        ),
    )
    state.run(
        state.client.update_project(arg, project_req), f"Updating {project_repr}..."
    )
    logger.info(f"Updated {project_repr}")


# HarborAsyncClient.delete_project()
@app.command("delete")
def delete_project(
    ctx: typer.Context,
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to delete (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the project name is an ID.",
    ),
) -> None:
    """Delete a project."""
    arg = get_project_arg(project_name_or_id, is_id)

    project_repr = get_project_repr(arg)

    state.run(state.client.delete_project(arg), f"Deleting {project_repr}...")


# HarborAsyncClient.get_project_summary()
@app.command("summary")
def get_project_summary(
    ctx: typer.Context,
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to delete (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the project name is an ID.",
    ),
) -> None:
    """Fetch project summary."""
    arg = get_project_arg(project_name_or_id, is_id)
    project_repr = get_project_repr(arg)
    summary = state.run(
        state.client.get_project_summary(arg), f"Fetching summary for {project_repr}..."
    )
    render_result(summary, ctx)


# HarborAsyncClient.get_project_scanner()
@scanner_cmd.command("get")
def get_project_scanner(
    ctx: typer.Context,
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to delete (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the project name is an ID.",
    ),
) -> None:
    arg = get_project_arg(project_name_or_id, is_id)
    scanner = state.run(state.client.get_project_scanner(arg))
    render_result(scanner, ctx)


# HarborAsyncClient.set_project_scanner()
@scanner_cmd.command("set")
def set_project_scanner(
    ctx: typer.Context,
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to delete (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the project name is an ID or not.",
    ),
    scanner_id: str = typer.Argument(
        ...,
        help="ID of the scanner to set.",
    ),
) -> None:
    arg = get_project_arg(project_name_or_id, is_id)
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
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to delete (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the project name is an ID or not.",
    ),
) -> None:
    arg = get_project_arg(project_name_or_id, is_id)
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
        return f"project with ID {arg}"


@overload
def get_project_arg(arg: str, is_id: Literal[False]) -> str:
    ...


@overload
def get_project_arg(arg: str, is_id: Literal[True]) -> int:
    ...


# this one looks unnecessary, but it isn't...
@overload
def get_project_arg(arg: str, is_id: bool) -> str | int:
    ...


def get_project_arg(arg: str, is_id: bool) -> str | int:
    """Converts a project argument to the correct type based on the is_id flag.

    We need to pass an int argument to harborapi if the project is specified by ID,
    and likewise a string if it's specified by name. This function converts the
    argument to the correct type based on the is_id flag.
    """
    if is_id:
        try:
            return int(arg)
        except ValueError:
            raise typer.BadParameter(f"Project ID {arg!r} is not an integer.")
    else:
        return arg


# Metadata commands (which are in their own category in Harbor API)

# HarborAsyncClient.get_project_metadata()
@metadata_cmd.command("get")
def get_project_metadata(
    ctx: typer.Context,
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to delete (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the project name is an ID or not.",
    ),
) -> None:
    """Get metadata for a project."""
    arg = get_project_arg(project_name_or_id, is_id)
    metadata = state.run(state.client.get_project_metadata(arg), "Fetching metadata...")
    render_result(metadata, ctx)


# HarborAsyncClient.set_project_metadata()
@metadata_cmd.command("set", short_help="Set metadata for a project.")
@inject_help(ProjectMetadata)
def set_project_metadata(
    ctx: typer.Context,
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the argument is a project ID or name (by default name)",
    ),
    public: Optional[str] = typer.Option(
        None,
    ),
    enable_content_trust: Optional[str] = typer.Option(
        None,
    ),
    enable_content_trust_cosign: Optional[str] = typer.Option(
        None,
    ),
    prevent_vul: Optional[str] = typer.Option(
        None,
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
    ),
    auto_scan: Optional[str] = typer.Option(
        None,
    ),
    reuse_sys_cve_whitelist: Optional[str] = typer.Option(
        None,
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
    arg = get_project_arg(project_name_or_id, is_id)

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
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to update (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the argument is a project ID or name (by default name)",
    ),
    field: str = typer.Argument(
        ...,
        help="The name of the field to get.",
    ),
) -> None:
    """Get a single field from the metadata for a project. NOTE: does not support table output currently."""
    arg = get_project_arg(project_name_or_id, is_id)
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
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project to update (interpreted as name by default).",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the argument is a project ID or name (by default name)",
    ),
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

    arg = get_project_arg(project_name_or_id, is_id)
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
    project_name_or_id: str = typer.Argument(
        ...,
        help="Name or ID of the project (interpreted as name by default).",
    ),
    field: str = typer.Argument(
        ...,
        help="The metadata field to delete.",
    ),
    is_id: bool = typer.Option(
        False,
        "--is-id",
        help="Whether the argument is a project ID or name (by default name)",
    ),
) -> None:
    """Delete a single field in the metadata for a project."""
    if field not in ProjectMetadata.__fields__:
        logger.warning(f"Field {field!r} is not a known project metadata field.")

    arg = get_project_arg(project_name_or_id, is_id)

    state.run(
        state.client.delete_project_metadata_entry(arg, field),
        f"Deleting metadata field {field!r}...",
    )
    logger.info(f"Deleted metadata field {field!r}.")
