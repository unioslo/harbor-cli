from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import TYPE_CHECKING
from typing import Union

import typer
from harborapi.exceptions import NotFound
from harborapi.ext.api import get_artifact
from harborapi.ext.api import get_artifact_vulnerabilities
from harborapi.ext.api import get_artifacts
from harborapi.ext.artifact import ArtifactInfo
from harborapi.ext.report import ArtifactReport
from harborapi.models import Label
from harborapi.models import Tag
from harborapi.models.scanner import Severity
from pydantic import BaseModel as PydanticBaseModel
from rich.table import Table
from strenum import StrEnum

from ...harbor.artifact import get_artifact_architecture
from ...harbor.artifact import get_artifact_os
from ...harbor.artifact import parse_artifact_name
from ...logs import logger
from ...models import ArtifactVulnerabilitySummary
from ...models import BaseModel
from ...models import Operator
from ...output.console import error
from ...output.console import exit_err
from ...output.console import exit_ok
from ...output.console import info
from ...output.console import warning
from ...output.prompts import bool_prompt
from ...output.prompts import check_enumeration_options
from ...output.prompts import delete_prompt
from ...output.render import render_result
from ...output.table._utils import get_table
from ...state import get_state
from ...style import render_cli_option
from ...style import render_cli_value
from ...style import render_warning
from ...utils.args import add_to_query
from ...utils.args import parse_commalist
from ...utils.commands import inject_resource_options
from ...utils.commands import OPTION_FORCE
from ...utils.commands import OPTION_QUERY
from ...utils.utils import parse_version_string
from ..help import ARTIFACT_HELP_STRING

if TYPE_CHECKING:
    from ...utils.utils import PackageVersion  # noqa: F401


state = get_state()

# Create a command group
app = typer.Typer(
    name="artifact",
    help="Manage artifacts.",
    no_args_is_help=True,
)

# Artifact subcommands
tag_cmd = typer.Typer(
    name="tag",
    help="Artifact tag commands",
    no_args_is_help=True,
)
label_cmd = typer.Typer(
    name="label",
    help="Artifact label commands",
    no_args_is_help=True,
)
vuln_cmd = typer.Typer(
    name="vulnerability",
    help="Artifact vulnerability commands",
    no_args_is_help=True,
)
app.add_typer(tag_cmd)
app.add_typer(label_cmd)
app.add_typer(vuln_cmd)


# get_artifacts()
@app.command("list")
@inject_resource_options()
def list_artifacts(
    ctx: typer.Context,
    project: List[str] = typer.Option(
        [],
        "--project",
        help=f"Project name(s). (e.g. {render_cli_value('library')}).",
        callback=parse_commalist,
    ),
    repo: List[str] = typer.Option(
        [],
        "--repo",
        help=f"Repository name(s).(e.g. {render_cli_value('hello-world')}).",
        callback=parse_commalist,
    ),
    query: Optional[str] = ...,  # type: ignore
    tag: List[str] = typer.Option(
        [],
        "--tag",
        help=f"Limit to artifacts with tag(s) (e.g. {render_cli_value('latest')}).",
        callback=parse_commalist,
    ),
    architecture: List[str] = typer.Option(
        [],
        "--arch",
        help=f"Limit to artifacts with architecture(s) (e.g. {render_cli_value('amd64,arm64')}).",
        callback=parse_commalist,
        metavar="arch",
    ),
    os: List[str] = typer.Option(
        [],
        "--os",
        help=f"Limit to artifacts with OS(es) (e.g. {render_cli_value('linux,freebsd')}).",
        callback=parse_commalist,
    ),
    with_report: bool = typer.Option(
        False,
        "--with-report",
        help="Include vulnerability report in output.",
    ),
    max_connections: int = typer.Option(
        5,
        "--max-connections",
        help=(
            "Maximum number of concurrent connections to use. "
            "Setting this too high can lead to severe performance degradation."
        ),
    ),
    # TODO: add ArtifactReport filtering options here
) -> None:
    """List artifacts in one or more projects and/or repositories."""
    # TODO: warn if no projects or repos match the given names

    # The presence of an asterisk trumps all other arguments
    # None signals that we want to enumerate over all projects
    if any(x == "*" for x in project) or not project:
        project = None  # type: ignore
    repositories = repo if repo else None
    query = add_to_query(query, tags=tag)

    # Confirm enumeration over all artifacts in all projects
    if project is None and repositories is None:
        check_enumeration_options(state, query=query, limit=None)

    artifacts = state.run(
        get_artifacts(
            state.client,
            projects=project,
            repositories=repositories,
            query=query,
            with_report=with_report,
        ),
        "Fetching artifacts...",
    )

    # extra_attrs fields cannot be filtered with an API query,
    # so we have to do it ourselves here
    results = artifacts
    if architecture:
        results = [
            a for a in results if get_artifact_architecture(a.artifact) in architecture
        ]
    if os:
        results = [a for a in results if get_artifact_os(a.artifact) in os]

    render_result(results, ctx)
    info(f"Fetched {len(results)} artifact(s).")


# delete_artifact()
@app.command("delete", no_args_is_help=True)
def delete_artifact(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete an artifact."""
    delete_prompt(state.config, force, resource="artifact", name=artifact)
    an = parse_artifact_name(artifact)

    try:
        state.run(
            state.client.delete_artifact(an.project, an.repository, an.reference),
            f"Deleting artifact {artifact}...",
        )
    except NotFound:
        exit_err(f"Artifact {artifact} not found.")
    else:
        info(f"Artifact {artifact} deleted.")


# copy_artifact()
@app.command("copy", no_args_is_help=True)
def copy_artifact(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    project: str = typer.Argument(
        ...,
        help="Destination project.",
    ),
    repository: str = typer.Argument(
        ...,
        help="Destination repository (without project name).",
    ),
) -> None:
    """Copy an artifact to a different repository."""

    # Warn user if they pass a project name in the repository name
    # e.g. project="foo", repository="foo/bar"
    # When it should be project="foo", repository="bar"
    # We can't prevent them from doing this in case this is a legitimate
    # use case, but in most cases it won't be so we need to warn them
    if project in repository:
        warning("Repository name contains project name, you likely don't want this.")

    try:
        resp = state.run(
            state.client.copy_artifact(project, repository, artifact),
            f"Copying artifact {artifact} to {project}/{repository}...",
        )
    except NotFound:
        exit_err(f"Artifact {artifact} not found.")
    else:
        info(f"Artifact {artifact} copied to {resp}.")


# HarborAsyncClient.get_artifact()
@app.command("get")
def get(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    with_vulnerabilities: bool = typer.Option(
        False,
        "--with-vuln",
        "-v",
        help="Include vulnerability report in output.",
    ),
    with_vuln_descriptions: bool = typer.Option(
        False,
        "--with-vuln-desc",
        "-d",
        help="Include descriptions of each vulnerability in the output.",
    )
    # TODO: --tag
) -> None:
    """Get information about a specific artifact."""

    an = parse_artifact_name(artifact)
    # Just use normal endpoint method for a single artifact
    art = state.run(
        get_artifact(state.client, an.project, an.repository, an.reference, with_report=with_vulnerabilities),  # type: ignore
        f"Fetching artifact(s)...",
    )

    # Hack to render vulnerabilities after the artifact in table mode
    # When we render in JSON mode we automatically render the report, but
    # in table mode we don't render the report by default
    # TODO: make this less hacky
    render_result(art, ctx, with_description=with_vuln_descriptions)


# HarborAsyncClient.get_artifact_tags()
@tag_cmd.command("list", no_args_is_help=True)
@inject_resource_options()
def list_artifact_tags(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    query: Optional[str] = ...,  # type: ignore
    sort: Optional[str] = ...,  # type: ignore
    page: int = ...,  # type: ignore
    page_size: int = ...,  # type: ignore
    limit: Optional[int] = ...,  # type: ignore
) -> None:
    """List tags for an artifact."""
    an = parse_artifact_name(artifact)
    tags = state.run(
        state.client.get_artifact_tags(
            project_name=an.project,
            repository_name=an.repository,
            reference=an.reference,
            query=query,
            sort=sort,
            page=page,
            page_size=page_size,
            limit=limit,
        ),
        f"Fetching tags for {an!r}...",
    )
    render_result(tags, ctx, artifact=artifact)


# create_artifact_tag()
@tag_cmd.command("create", no_args_is_help=True)
def create_artifact_tag(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    tag: str = typer.Argument(..., help="Name of the tag to create."),
    # signed (probably not. Deprecated in v2.9.0)
    # immutable?
) -> None:
    """Create a tag for an artifact."""
    an = parse_artifact_name(artifact)
    # NOTE: We might need to fetch repo and artifact IDs
    t = Tag(name=tag)
    location = state.run(
        state.client.create_artifact_tag(an.project, an.repository, an.reference, t),
        f"Creating tag {tag!r} for {artifact}...",
    )
    info(f"Created {tag!r} for {artifact}: {location}")


# delete_artifact_tag()
@tag_cmd.command("delete", no_args_is_help=True)
def delete_artifact_tag(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    tag: str = typer.Argument(..., help="Name of the tag to delete."),
    force: bool = OPTION_FORCE,
) -> None:
    """Delete a tag for an artifact."""
    delete_prompt(state.config, force, resource="tag", name=tag)

    an = parse_artifact_name(artifact)
    # NOTE: We might need to fetch repo and artifact IDs

    state.run(
        state.client.delete_artifact_tag(an.project, an.repository, an.reference, tag),
        f"Deleting tag {tag!r} for {artifact}...",
    )


# add_artifact_label()
@label_cmd.command("add", no_args_is_help=True)
def add_artifact_label(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Name of the label.",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        help="Description of the label.",
    ),
    color: Optional[str] = typer.Option(
        None,
        "--color",
        help="Label color.",
    ),
    scope: Optional[str] = typer.Option(
        None,
        "--scope",
        help="Scope of the label.",
    ),
) -> None:
    """Add a label to an artifact."""
    # TODO: add parameter validation. Name is probably required?
    # Otherwise, we can just leave validation to the API, and
    # print a default error message.
    an = parse_artifact_name(artifact)
    label = Label(
        name=name,
        description=description,
        color=color,
        scope=scope,
    )
    state.run(
        state.client.add_artifact_label(an.project, an.repository, an.reference, label),
        f"Adding label {label.name!r} to {artifact}...",
    )
    info(f"Added label {label.name!r} to {artifact}.")


# HarborAsyncClient.delete_artifact_label()
@label_cmd.command("delete", no_args_is_help=True)
def delete_artifact_label(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
    label_id: int = typer.Argument(
        ...,
        help="ID of the label to delete.",
    ),
    force: bool = OPTION_FORCE,
) -> None:
    """Remove a label from an artifact."""
    delete_prompt(state.config, force, resource="label", name=str(label_id))
    an = parse_artifact_name(artifact)
    state.run(
        state.client.delete_artifact_label(
            an.project, an.repository, an.reference, label_id
        ),
        f"Deleting label {label_id} from {artifact}...",
    )


# HarborAsyncClient.get_artifact_vulnerabilities()
# HarborAsyncClient.get_artifact_accessories()
@app.command("accessories")
def get_accessories(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
) -> None:
    """Get accessories for an artifact."""
    an = parse_artifact_name(artifact)
    accessories = state.run(
        state.client.get_artifact_accessories(an.project, an.repository, an.reference),
        f"Getting accessories for {artifact}...",
    )
    render_result(accessories, ctx)


# HarborAsyncClient.get_artifact_build_history()
@app.command("buildhistory", no_args_is_help=True)
def get_buildhistory(
    ctx: typer.Context,
    artifact: str = typer.Argument(
        ...,
        help=ARTIFACT_HELP_STRING,
    ),
) -> None:
    """Get the build history of an artifact."""
    an = parse_artifact_name(artifact)
    history = state.run(
        state.client.get_artifact_build_history(
            an.project, an.repository, an.reference
        ),
        f"Getting build history for {artifact}...",
    )
    render_result(history, ctx, artifact=artifact)


class DeletionReason(StrEnum):
    """Reasons for deleting an artifact."""

    AGE = "age"
    SEVERITY = "severity"


class ArtifactDeletion:
    """Encapsulates artifaction deletion checks."""

    deletion_time = datetime.now()

    def __init__(
        self,
        artifact: ArtifactInfo,
        operator: Operator,
        age: int | None = None,
        severity: Severity | None = None,
        except_project: str | None = None,
        except_repo: str | None = None,
        except_tag: str | None = None,
    ) -> None:
        self.artifact = artifact
        self.operator = operator
        # Matching criteria
        self.age = age
        self.severity = severity
        # Exclusion criteria
        self.except_project = except_project
        self.except_repo = except_repo
        self.except_tag = except_tag

        # Construct a dictionary from the criteria passed in
        self.criteria = {}  # type: dict[str, bool]
        if age is not None:
            self.criteria[DeletionReason.AGE] = False
        if severity is not None:
            self.criteria[DeletionReason.SEVERITY] = False

    @property
    def reasons(self) -> list[str]:
        return [k for k, v in self.criteria.items() if v]

    def should_delete(self) -> bool:
        """Determines if the artifact should be deleted or not.
        Returns a tuple of (should_delete, reason).

        Returns
        -------
        bool
            True if the artifact should be deleted, False otherwise.
        """
        a = self.artifact  # increase readability

        # Check exclusions first
        if self.except_project and re.search(self.except_project, a.project_name):
            return False
        if self.except_project and re.search(self.except_project, a.repository_name):
            return False
        if self.except_tag and a.artifact.tags:
            if any(  # type: ignore # mypy can't infer the type of a.artifact.tags for some reason
                re.search(self.except_tag, tag)
                for tag in filter(None, (t.name for t in a.artifact.tags))
            ):
                return False

        # Check potential matches
        if self.age and self.exceeds_age():
            self.criteria[DeletionReason.AGE] = True
        if self.severity and self.exceeds_severity():
            self.criteria[DeletionReason.SEVERITY] = True

        # Check if we have any matches.
        return self._check_criteria()

    def exceeds_severity(self) -> bool:
        if self.severity and self.artifact.artifact.scan is not None:
            overview = self.artifact.artifact.scan
            if not overview.severity_enum:
                return False
            if overview.severity_enum >= self.severity:
                return True
        return False

    def exceeds_age(self) -> bool:
        if self.age is not None and self.artifact.artifact.push_time is not None:
            tz = self.artifact.artifact.push_time.tzinfo
            now = datetime.now(tz=tz)
            td = now - self.artifact.artifact.push_time
            if td.days > self.age:
                return True
        return False

    def _check_criteria(self) -> bool:
        if self.operator == Operator.OR:
            return any(self.criteria.values())
        elif self.operator == Operator.AND:
            return all(self.criteria.values())
        elif self.operator == Operator.XOR:
            return sum(self.criteria.values()) == 1
        else:
            raise ValueError(f"Unknown operator {self.operator}")


# Declare this model here, so we can pass it directly to render_result,
# which will call __rich_console__ on it.
# It's an ad-hoc model that doesn't need its own entry in output/tables/__init__.py
class ScheduledArtifactDeletion(PydanticBaseModel):
    """Encapsulates an artifact deletion scheduled for a future time."""

    artifacts: Dict[str, List[Union[DeletionReason, str]]]

    def as_table(self, **kwargs) -> Table:  # type: ignore
        from ...output.table._utils import get_table

        table = get_table(
            "Artifact", list(self.artifacts.keys()), columns=["Artifact", "Reasons"]
        )
        for artifact, reasons in self.artifacts.items():
            table.add_row(artifact, ", ".join(reasons))
        yield table


@app.command("clean")
def cleanup_artifacts(
    ctx: typer.Context,
    # Target options
    project: Optional[List[str]] = typer.Option(
        None,
        "--project",
        help="Project(s) to delete artifacts from. If not specified, all projects will be considered.",
        callback=parse_commalist,
    ),
    repository: Optional[List[str]] = typer.Option(
        None,
        "--repo",
        help="Repository name(s) to delete artifacts from. If not specified, all repositories in the matched project(s) will be considered.",
        callback=parse_commalist,
    ),
    # Matching options
    age: Optional[int] = typer.Option(
        None,
        "--age",
        help="CRITERIA: Delete artifacts older than the specified number of days.",
    ),
    severity: Optional[Severity] = typer.Option(
        None,
        "--severity",
        help="CRITERIA: Delete all artifacts with the given severity or higher.",
    ),
    # Matching operator
    operator: Operator = typer.Option(
        Operator.AND.value,
        "--operator",
        help="Operator to use when matching multiple criteria.",
    ),
    # Exclusion options
    except_project: Optional[str] = typer.Option(
        None,
        "--except-project",
        help="Regex pattern for excluding artifacts from projects.",
    ),
    except_repo: Optional[str] = typer.Option(
        None,
        "--except-repo",
        help="Regex pattern for excluding artifacts from repositories.",
    ),
    except_tag: Optional[str] = typer.Option(
        None,
        "--except-tag",
        help="Regex pattern for artifacts with tags to exclude from deletion.",
    ),
    max_count: Optional[int] = typer.Option(
        None,
        "--max",
        help="Abort deletion if this number of artifacts would be deleted.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dryrun",
        help="Show which artifacts would be deleted, but don't do anything.",
    ),
    force: bool = OPTION_FORCE,
    exit_on_error: bool = typer.Option(
        False,
        "--exit-on-error",
        help="Abort the operation and exit with non-zero exit code if an artifact cannot be deleted.",
    ),
) -> None:
    """Bulk delete artifacts that match one or more conditions."""
    if not project and not repository:
        warning(
            "Not specifying any projects or repositories could be very dangerous and slow."
        )

    artifacts = state.run(
        get_artifacts(
            state.client,
            projects=project or None,
            repositories=repository or None,
        ),
        "Fetching artifacts...",
    )

    to_delete = []  # type: list[ArtifactDeletion]

    # Determine which artifacts to delete
    for artifact in artifacts:
        d = ArtifactDeletion(
            artifact=artifact,
            operator=operator,
            age=age,
            severity=severity,
            except_project=except_project,
            except_repo=except_repo,
            except_tag=except_tag,
        )
        if d.should_delete():
            if not artifact.artifact.digest:
                exit_err(
                    f"Artifact {artifact.name_with_tag!r} has no digest, this should not happen. Check the logs for more information.",
                    artifact=artifact.model_dump(),
                )
            to_delete.append(d)
            logger.debug(
                f"Scheduling {artifact.name_with_digest} for deletion. Reason(s): {', '.join(reason for reason in d.reasons)}",
                extra=dict(artifact=artifact.name_with_digest, reasons=d.criteria),
            )

    if max_count and len(to_delete) > max_count:
        exit_err(
            f"Aborting. Would delete {len(to_delete)} artifacts, which is more than the maximum of {max_count}.",
        )

    res = ScheduledArtifactDeletion(
        artifacts={
            deletion.artifact.name_with_digest: deletion.reasons
            for deletion in to_delete
        }
    )

    info(f"Will delete {len(to_delete)} artifacts:")
    render_result(res, ctx)

    if dry_run:
        return  # exit early

    # Show prompt after we have found the artifacts
    delete_prompt(state.config, force=force, dry_run=dry_run, resource="artifacts")

    for deletion in to_delete:
        artifact = deletion.artifact
        try:
            state.run(
                state.client.delete_artifact(
                    project_name=artifact.project_name,
                    repository_name=artifact.repository_name,
                    reference=artifact.artifact.digest,  # type: ignore # we know this isn't None
                ),
                f"Deleting {deletion.artifact.name_with_digest}...",
            )
            info(f"Deleted {artifact.name_with_digest}")
        except Exception as e:
            msg = f"Failed to delete {artifact.name_with_digest}: {e}"
            kwargs = {
                "artifact": artifact.name_with_digest,
                "error": str(e),
            }
            if exit_on_error:
                exit_err(msg, **kwargs)  # type: ignore # wrong mypy err? this isn't argument 2
            else:
                error(msg, **kwargs, exc_info=True)


class AffectedArtifact(BaseModel):
    artifact: str
    tags: List[str] = []
    vulnerabilities: Set[str] = set()
    packages: Set[str] = set()

    @property
    def vulnerabilities_str(self) -> str:
        return ", ".join(self.vulnerabilities)

    @property
    def packages_str(self) -> str:
        return ", ".join(self.packages)

    @property
    def tags_str(self) -> str:
        return ", ".join(self.tags or [])


def get_artifactinfo_name(artifact: ArtifactInfo) -> str:
    return artifact.name_with_tag if artifact.tags else artifact.name_with_digest_full


class AffectedArtifactList(BaseModel):
    artifacts: Dict[str, AffectedArtifact] = {}

    def add(
        self,
        artifacts: List[ArtifactInfo],
        vulnerabilities: Optional[List[str]] = None,
        packages: Optional[List[str]] = None,
    ) -> None:
        for artifact in artifacts:
            # TODO: assert that either vulnerability or package is set
            if artifact.artifact.tags:
                tags = [tag.name for tag in artifact.artifact.tags if tag.name]
            else:
                tags = []
            a = AffectedArtifact(
                artifact=get_artifactinfo_name(artifact),
                tags=tags,
                vulnerabilities=vulnerabilities or [],  # type: ignore # coerced to set in model
                packages=packages or [],  # type: ignore # coerced to set in model
                # TODO: add exact package versions somehow
            )
            self.update(a)

    def update(self, artifact: AffectedArtifact) -> None:
        a = self.artifacts.get(artifact.artifact)
        if not a:
            self.artifacts[artifact.artifact] = artifact
            return
        a.vulnerabilities.update(artifact.vulnerabilities)
        a.packages.update(artifact.packages)

    def as_table(self, **kwargs: Any) -> Iterable[Table]:  # type: ignore
        table = get_table(
            "Artifacts",
            columns=[
                "Name",
                "Tags",
                "Matches",
            ],
        )

        for artifact in self.artifacts.values():
            match_table = get_table(columns=["Vulnerabilities", "Packages"])
            match_table.add_row(artifact.vulnerabilities_str, artifact.packages_str)
            table.add_row(
                artifact.artifact,
                artifact.tags_str,
                match_table,
            )
        yield table


class ArtifactSummarySorting(StrEnum):
    total = "total"
    severity = "severity"
    name = "name"
    age = "age"


class SortOrder(StrEnum):
    asc = "asc"
    desc = "desc"

    @property
    def reverse(self) -> bool:
        return self == SortOrder.desc


@vuln_cmd.command("summary")
def list_artifact_vulnerabilities_summary(
    ctx: typer.Context,
    project: List[str] = typer.Option(
        [],
        "--project",
        help="Name of projects to check.",
        callback=parse_commalist,
    ),
    repo: List[str] = typer.Option(
        [],
        "--repo",
        help="Name of repositories to check.",
        callback=parse_commalist,
    ),
    query: Optional[str] = OPTION_QUERY,
    sort: ArtifactSummarySorting = typer.Option(
        ArtifactSummarySorting.total,
        "--sort",
        help="Artifact attribute to sort by.",
        case_sensitive=False,
    ),
    order: SortOrder = typer.Option(
        SortOrder.desc,
        "--order",
        help="Sorting order of artifacts.",
        case_sensitive=False,
    ),
    full_digest: bool = typer.Option(
        False,
        "--full-digest",
        help="Show full artifact digests.",
    ),
) -> None:
    """Show a summary of vulnerabilities for artifacts in a project or repository."""
    # TODO: check_enumeration_options when no projects and no repos
    result = state.run(
        get_artifacts(
            state.client,
            projects=project if project else None,
            repositories=repo if repo else None,
            query=query,
            with_report=True,
        ),
        "Fetching artifacts...",
    )

    # fmt: off
    if sort == ArtifactSummarySorting.total:
        # Most -> Least (total vulnerabilities)
        def sort_key(a: ArtifactInfo) -> int:
            try:
                return a.artifact.scan.summary.total or 0  # type: ignore
            except AttributeError:
                return 0
    elif sort == ArtifactSummarySorting.severity:
        # Number of critical vulnerabilities

        # TODO: this could take into account other severities as well
        # And we could just weight them by severity.
        #
        # Weighting:
        #   Critical: 10
        #   High: 5
        #   Medium: 2
        #   Low: 1
        #   Negligible: 0
        #   Unknown: 0
        #
        # Example:
        # try:
        #    summary = a.artifact.scan.summary
        # except AttributeError:
        #    return 0
        #
        # for attr in ["critical", ...]:
        #    if getattr(summary, attr):
        #        return getattr(summary, attr) * weight
        # return 0
        def sort_key(a: ArtifactInfo) -> int:
            try:
                return a.artifact.scan.summary.critical or 0  # type: ignore
            except AttributeError:
                return 0
    elif sort == ArtifactSummarySorting.name:
        # A -> Z
        def sort_key(a: ArtifactInfo) -> str: # type: ignore
            return a.name_with_digest_full
    elif sort == ArtifactSummarySorting.age:
        # new -> old
        def sort_key(a: ArtifactInfo) -> float: # type: ignore
            try:
                return a.artifact.push_time.timestamp()  # type: ignore
            except AttributeError:
                return 0.0
    else:
        raise ValueError(f"Unknown sorting criteria: {sort}")
    # fmt: on
    result = sorted(result, key=sort_key, reverse=order.reverse)

    summary = [ArtifactVulnerabilitySummary.from_artifactinfo(r) for r in result]
    render_result(summary, ctx, vuln_summary=True, full_digest=full_digest)


# harborapi.ext.api.get_artifact
@vuln_cmd.command("find", hidden=True)
def get_vulnerabilities(
    ctx: typer.Context,
    cve: List[str] = typer.Option(
        [],
        "--cve",
        help="CVE ID(s) to search for.",
        callback=parse_commalist,
    ),
    package: List[str] = typer.Option(
        [],
        "--package",
        # TODO: fix formatting of this message (very strange)
        help=(
            "Name of package(s) used by artifacts to search for. "
            "Can contain a semver min and max range, similar to PEP 440, e.g. "
            f"{render_cli_value('foo>=1.0.0,<2.0.0')}. "
            f"{render_warning('Minimum and maximum version limits are always inclusive (i.e. >= and > are the same)')}"
        ),
        # cant use parse_commalist here because the version strings can contain commas
    ),
    project: Optional[List[str]] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project(s) to get vulnerabilities for. If not specified, all projects will be considered.",
        callback=parse_commalist,
    ),
    repo: Optional[List[str]] = typer.Option(
        None,
        "--repo",
        "-r",
        help=(
            "Repositories to search in. "
            "Can be either full name ('project/repo') or repo name only ('repo'). "
            "If not specified, all repositories in the project(s) will be considered."
        ),
        callback=parse_commalist,
    ),
    tags: Optional[List[str]] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Artifact tag(s) to filter for. If not specified, all tags in the repository(s) will be considered.",
        callback=parse_commalist,
    ),
    max_connections: int = typer.Option(
        5,
        "--max-connections",
        help="Maximum number of concurrent connections to the Harbor API.",
    ),
    operator: Operator = typer.Option(
        Operator.OR.value,
        "--operator",
        help="Operator to use when querying a combination of multiple CVEs or packages.",
    ),
) -> None:
    """Find artifacts affected by a given CVE or vulnerable package.

    :information: The output of this command is slated to change in the future.
    It desperately needs a facelift. Hidden until this is resolved.
    """
    # Check that we have at least one CVE or package
    if not any([cve, package]):
        exit_err("One or more CVEs or packages is required.")
    if operator not in [Operator.AND, Operator.OR]:
        exit_err(f"Unsupported operator: {operator.value!r}")

    # Warning/prompting for large operations
    if (not project and not repo) and state.config.general.confirm_enumeration:
        warning(
            f"Fetching vulnerabilities for every artifact in the registry can "
            "take a long time (minutes to hours). "
            f"Use {render_cli_option('--project')} and {render_cli_option('--repo')} "
            "to limit the scope of the operation."
        )
        if not bool_prompt("Continue", default=False):
            exit_ok()
    elif not project:
        warning("Fetching from all projects can be slow even with a repository filter.")

    # Check our package versions for validity _before_ we fetch the artifacts
    packages = []  # type: list[PackageVersion]
    for package_version in package:
        try:
            pkg = parse_version_string(package_version)
        except Exception as e:
            exit_err(f"Invalid package version: {package_version}", exception=e)
        packages.append(pkg)

    artifacts = state.run(
        get_artifact_vulnerabilities(
            state.client, projects=project, repositories=repo, tags=tags
        ),
        f"Fetching artifacts...",
    )

    report = ArtifactReport(artifacts)

    affected = AffectedArtifactList()
    if operator == Operator.OR:
        # Each match is added to the list of affected artifacts
        # The list handles duplicates
        for c in cve:
            with_cve = report.with_cve(c).artifacts
            affected.add(with_cve, vulnerabilities=[c])
        for pkg in packages:
            with_package = report.with_package(
                pkg.package,
                min_version=pkg.min_version,
                max_version=pkg.max_version,
                case_sensitive=False,
            ).artifacts
            affected.add(with_package, packages=[pkg.package])
    elif operator == Operator.AND:
        # We overwrite the report variable until we have exhausted all conditions
        for c in cve:
            report = report.with_cve(c)
        for pkg in packages:
            report = report.with_package(
                pkg.package,
                min_version=pkg.min_version,
                max_version=pkg.max_version,
                case_sensitive=False,
            )
        affected.add(
            report.artifacts,
            vulnerabilities=cve,
            packages=[p.package for p in packages],
        )
    else:
        exit_err(f"Unsupported: {operator}")  # same check as above for safety

    render_result(affected, ctx)
