from __future__ import annotations

from typing import Optional

import typer
from harborapi.models import Configurations

from ...logs import logger
from ...output.console import console
from ...state import state
from ...utils import inject_help

# Create a command group
app = typer.Typer(
    name="config",
    help="Manage Harbor configuration.",
    no_args_is_help=True,
)


@app.command("get", no_args_is_help=True)
def get_config(ctx: typer.Context) -> None:
    """Fetch the Harbor configuration."""
    logger.info(f"Fetching system info...")
    system_info = state.loop.run_until_complete(state.client.get_config())
    console.print(system_info)


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
    ),
    self_registration: Optional[bool] = typer.Option(
        None,
        "--self-registration",
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
            "(we keep parity with harbor naming schemes, and that's what the spec calls this field.)"
        ),
    ),
    http_authproxy_verify_cert: Optional[bool] = typer.Option(
        None,
        "--http-authproxy-verify-cert",
    ),
    http_authproxy_skip_search: Optional[bool] = typer.Option(
        None,
        "--http-authproxy-skip-search",
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
    ),
    oidc_auto_onboard: Optional[bool] = typer.Option(
        None,
        "--oidc-auto-onboard",
    ),
    oidc_extra_redirect_parms: Optional[str] = typer.Option(
        None,
        "--oidc-extra-redirect-parms",
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
        "--notification-enable",
    ),
    quota_per_project_enable: Optional[bool] = typer.Option(
        None,
        "--quota-per-project-enable",
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
    ),
) -> None:
    """Update the configuration of Harbor."""
    logger.info("Updating configuration...")
    state.run(
        state.client.update_config(
            Configurations(
                auth_mode=auth_mode,
                email_from=email_from,
                email_host=email_host,
                email_identity=email_identity,
                email_insecure=email_insecure,
                email_password=email_password,
                email_port=email_port,
                email_ssl=email_ssl,
                email_username=email_username,
                ldap_base_dn=ldap_base_dn,
                ldap_filter=ldap_filter,
                ldap_group_base_dn=ldap_group_base_dn,
                ldap_group_admin_dn=ldap_group_admin_dn,
                ldap_group_attribute_name=ldap_group_attribute_name,
                ldap_group_search_filter=ldap_group_search_filter,
                ldap_group_search_scope=ldap_group_search_scope,
                ldap_scope=ldap_scope,
                ldap_search_dn=ldap_search_dn,
                ldap_search_password=ldap_search_password,
                ldap_timeout=ldap_timeout,
                ldap_uid=ldap_uid,
                ldap_url=ldap_url,
                ldap_verify_cert=ldap_verify_cert,
                ldap_group_membership_attribute=ldap_group_membership_attribute,
                project_creation_restriction=project_creation_restriction,
                read_only=read_only,
                self_registration=self_registration,
                token_expiration=token_expiration,
                uaa_client_id=uaa_client_id,
                uaa_client_secret=uaa_client_secret,
                uaa_endpoint=uaa_endpoint,
                uaa_verify_cert=uaa_verify_cert,
                http_authproxy_endpoint=http_authproxy_endpoint,
                http_authproxy_tokenreview_endpoint=http_authproxy_tokenreview_endpoint,
                http_authproxy_admin_groups=http_authproxy_admin_groups,
                http_authproxy_admin_usernames=http_authproxy_admin_usernames,
                http_authproxy_verify_cert=http_authproxy_verify_cert,
                http_authproxy_skip_search=http_authproxy_skip_search,
                http_authproxy_server_certificate=http_authproxy_server_certificate,
                oidc_name=oidc_name,
                oidc_endpoint=oidc_endpoint,
                oidc_client_id=oidc_client_id,
                oidc_client_secret=oidc_client_secret,
                oidc_groups_claim=oidc_groups_claim,
                oidc_admin_group=oidc_admin_group,
                oidc_scope=oidc_scope,
                oidc_user_claim=oidc_user_claim,
                oidc_verify_cert=oidc_verify_cert,
                oidc_auto_onboard=oidc_auto_onboard,
                oidc_extra_redirect_parms=oidc_extra_redirect_parms,
                robot_token_duration=robot_token_duration,
                robot_name_prefix=robot_name_prefix,
                notification_enable=notification_enable,
                quota_per_project_enable=quota_per_project_enable,
                storage_per_project=storage_per_project,
                audit_log_forward_endpoint=audit_log_forward_endpoint,
                skip_audit_log_database=skip_audit_log_database,
            )
        )
    )
    logger.info("Configuration updated.")
