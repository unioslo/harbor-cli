from __future__ import annotations

from typing import Any
from typing import Optional

import typer
from harborapi.models import Configurations
from harborapi.models import ConfigurationsResponse

from ...output.console import exit_err
from ...output.console import info
from ...output.render import render_result
from ...state import get_state
from ...utils.args import model_params_from_ctx
from ...utils.commands import inject_help

state = get_state()

app = typer.Typer(
    name="config",
    help="Manage Harbor configuration.",
    no_args_is_help=True,
)


def flatten_config_response(response: ConfigurationsResponse) -> dict[str, Any]:
    """Flattens a ConfigurationsResponse object to a single level, removing
    any information about whether the fields are editable or not.

    Examples
    -------
    >>> response = ConfigurationsResponse(
    ...     auth_mode=StringConfigItem(value="db_auth", editable=True),
    ... )
    >>> response.dict() # just to show the structure
    {'auth_mode': {'value': 'db_auth', 'editable': True}}
    >>> flatten_config_response(response)
    {'auth_mode': 'db_auth'}

    Parameters
    ----------
    response : ConfigurationsResponse
        A ConfigurationsResponse object from the Harbor API.
        Fields are either None or a {String,Int,Bool}ConfigItem object,
        that each have the fields "value" and "editable".

    Returns
    -------
    dict[str, Any]
        A flattened dictionary with the "value" fields of the
        {String,Int,Bool}ConfigItem objects.
    """
    # A ConfigurationsResponse contains {String,Int,Bool}ConfigItem objects
    # which has the fields "value" and "editable".
    c = response.model_dump()
    for key, value in list(c.items()):
        if value is None:
            del c[key]
        if not isinstance(value, dict):
            # NOTE: continue or delete?
            # add flag to keep or delete?
            continue
        v = value.get("value")
        c[key] = v
    return c


@app.command("get")
def get_config(
    ctx: typer.Context,
    flatten: bool = typer.Option(
        True,
        help="Flatten config response to a single level.",
    ),
) -> None:
    """Fetch the current Harbor configuration."""
    system_info = state.run(state.client.get_config(), "Fetching system info...")
    if flatten:
        # In order to print a flattened response, we turn it from a
        # ConfigurationsResponse to a Configurations object.
        flattened = flatten_config_response(system_info)
        c = Configurations.model_validate(flattened)
        render_result(c, ctx)
    else:
        render_result(system_info, ctx)


# TODO: fix Optional[bool] options
@app.command("update", no_args_is_help=True)
@inject_help(Configurations)
def update_config(
    ctx: typer.Context,
    auth_mode: Optional[str] = typer.Option(
        None,
        "--auth-mode",
    ),
    email_from: Optional[str] = typer.Option(
        None,
        "--email-from",
    ),
    email_host: Optional[str] = typer.Option(
        None,
        "--email-host",
    ),
    email_identity: Optional[str] = typer.Option(
        None,
        "--email-identity",
    ),
    email_insecure: Optional[bool] = typer.Option(
        None,
        "--email-insecure",
        is_flag=False,
    ),
    email_password: Optional[str] = typer.Option(
        None,
        "--email-password",
    ),
    email_port: Optional[int] = typer.Option(
        None,
        "--email-port",
    ),
    email_ssl: Optional[bool] = typer.Option(
        None,
        "--email-ssl",
        is_flag=False,
    ),
    email_username: Optional[str] = typer.Option(
        None,
        "--email-username",
    ),
    ldap_base_dn: Optional[str] = typer.Option(
        None,
        "--ldap-base-dn",
    ),
    ldap_filter: Optional[str] = typer.Option(
        None,
        "--ldap-filter",
    ),
    ldap_group_base_dn: Optional[str] = typer.Option(
        None,
        "--ldap-group-base-dn",
    ),
    ldap_group_admin_dn: Optional[str] = typer.Option(
        None,
        "--ldap-group-admin-dn",
    ),
    ldap_group_attribute_name: Optional[str] = typer.Option(
        None,
        "--ldap-group-attribute-name",
    ),
    ldap_group_search_filter: Optional[str] = typer.Option(
        None,
        "--ldap-group-search-filter",
    ),
    ldap_group_search_scope: Optional[int] = typer.Option(
        None,
        "--ldap-group-search-scope",
    ),
    ldap_scope: Optional[int] = typer.Option(
        None,
        "--ldap-scope",
    ),
    ldap_search_dn: Optional[str] = typer.Option(
        None,
        "--ldap-search-dn",
    ),
    ldap_search_password: Optional[str] = typer.Option(
        None,
        "--ldap-search-password",
    ),
    ldap_timeout: Optional[int] = typer.Option(
        None,
        "--ldap-timeout",
    ),
    ldap_uid: Optional[str] = typer.Option(
        None,
        "--ldap-uid",
    ),
    ldap_url: Optional[str] = typer.Option(
        None,
        "--ldap-url",
    ),
    ldap_verify_cert: Optional[bool] = typer.Option(
        None,
        "--ldap-verify-cert",
        is_flag=False,
    ),
    ldap_group_membership_attribute: Optional[str] = typer.Option(
        None,
        "--ldap-group-membership-attribute",
    ),
    project_creation_restriction: Optional[str] = typer.Option(
        None,
        "--project-creation-restriction",
    ),
    read_only: Optional[bool] = typer.Option(
        None,
        "--read-only",
        is_flag=False,
    ),
    self_registration: Optional[bool] = typer.Option(
        None,
        "--self-registration",
        is_flag=False,
    ),
    token_expiration: Optional[int] = typer.Option(
        None,
        "--token-expiration",
    ),
    uaa_client_id: Optional[str] = typer.Option(
        None,
        "--uaa-client-id",
    ),
    uaa_client_secret: Optional[str] = typer.Option(
        None,
        "--ua",
    ),
    uaa_endpoint: Optional[str] = typer.Option(
        None,
        "--uaa-endpoint",
    ),
    uaa_verify_cert: Optional[bool] = typer.Option(
        None,
        "--uaa-verify-cert",
        is_flag=False,
    ),
    http_authproxy_endpoint: Optional[str] = typer.Option(
        None,
        "--http-authproxy-endpoint",
    ),
    http_authproxy_tokenreview_endpoint: Optional[str] = typer.Option(
        None,
        "--http-authproxy-tokenreview-endpoint",
    ),
    http_authproxy_admin_groups: Optional[str] = typer.Option(
        None,
        "--http-authproxy-admin-groups",
    ),
    http_authproxy_admin_usernames: Optional[str] = typer.Option(
        None,
        "--http-authproxy-admin-usernames",
        help=(
            "The username of the user with admin privileges. "
            "NOTE: ONLY ACCEPTS A SINGLE USERNAME DESPITE NAMING SCHEME IMPLYING OTHERWISE! "
        ),
    ),
    http_authproxy_verify_cert: Optional[bool] = typer.Option(
        None,
        "--http-authproxy-verify-cert",
        is_flag=False,
    ),
    http_authproxy_skip_search: Optional[bool] = typer.Option(
        None,
        "--http-authproxy-skip-search",
        is_flag=False,
    ),
    http_authproxy_server_certificate: Optional[str] = typer.Option(
        None,
        "--http-authproxy-server-certificate",
    ),
    oidc_name: Optional[str] = typer.Option(
        None,
        "--oidc-name",
    ),
    oidc_endpoint: Optional[str] = typer.Option(
        None,
        "--oidc-endpoint",
    ),
    oidc_client_id: Optional[str] = typer.Option(
        None,
        "--oidc-client-id",
    ),
    oidc_client_secret: Optional[str] = typer.Option(
        None,
        "--oidc-client-secret",
    ),
    oidc_groups_claim: Optional[str] = typer.Option(
        None,
        "--oidc-groups-claim",
    ),
    oidc_admin_group: Optional[str] = typer.Option(
        None,
        "--oidc-admin-group",
    ),
    oidc_scope: Optional[str] = typer.Option(
        None,
        "--oidc-scope",
    ),
    oidc_user_claim: Optional[str] = typer.Option(
        None,
        "--oidc-user-claim",
    ),
    oidc_verify_cert: Optional[bool] = typer.Option(
        None,
        "--oidc-verify-cert",
        is_flag=False,
    ),
    oidc_auto_onboard: Optional[bool] = typer.Option(
        None,
        "--oidc-auto-onboard",
        is_flag=False,
    ),
    # TODO: fix spelling when we add alias in harborapi
    oidc_extra_redirect_parms: Optional[str] = typer.Option(
        None,
        help=(
            "Extra parameters to add when redirect request to OIDC provider. "
            "WARNING: 'parms' not 'parAms', due to Harbor spelling parity (blame them)."
        ),
    ),
    robot_token_duration: Optional[int] = typer.Option(
        None,
        "--robot-token-duration",
    ),
    robot_name_prefix: Optional[str] = typer.Option(
        None,
        "--robot-name-prefix",
    ),
    notification_enable: Optional[bool] = typer.Option(
        None,
        "--notifications",
        is_flag=False,
    ),
    quota_per_project_enable: Optional[bool] = typer.Option(
        None,
        "--quota-per-project",
        is_flag=False,
    ),
    storage_per_project: Optional[int] = typer.Option(
        None,
        "--storage-per-project",
    ),
    audit_log_forward_endpoint: Optional[str] = typer.Option(
        None,
        "--audit-log-forward-endpoint",
    ),
    skip_audit_log_database: Optional[bool] = typer.Option(
        None,
        "--skip-audit-log-database",
        is_flag=False,
    ),
) -> None:
    """Update the Harbor configuration.

    One or more configuration parameters must be provided."""
    info("Updating configuration...")
    params = model_params_from_ctx(ctx, Configurations)
    if not params:
        exit_err("No configuration parameters provided.")

    current_config = state.run(
        state.client.get_config(),
        "Fetching current configuration...",
    )
    # get_config fetches a ConfigurationsResponse object, but we need
    # to pass a Configurations object to update_config. To get the
    # correct parameters to pass to Configurations, we need to flatten
    # the dict representation of the ConfigurationsResponse object
    # to create a dict of key:ConfigItem.value.
    c = flatten_config_response(current_config)
    c.update(params)

    configuration = Configurations.model_validate(c)

    state.run(
        state.client.update_config(configuration),
        "Updating configuration...",
    )
    info("Configuration updated.")
