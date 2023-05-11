from __future__ import annotations

from typing import Optional

import typer
from harborapi.models.models import LdapConf

from ...output.render import render_result
from ...state import get_state
from ...utils.args import model_params_from_ctx
from ...utils.commands import inject_help

state = get_state()

# Create a command group
app = typer.Typer(
    name="ldap",
    help="LDAP configuration",
    no_args_is_help=True,
)
search_cmd = typer.Typer(
    name="search",
    help="Search for users and groups in LDAP",
    no_args_is_help=True,
)
app.add_typer(search_cmd)


@app.command("ping")
@inject_help(LdapConf)
def ping(
    ctx: typer.Context,
    ldap_url: str = typer.Option(None, "--url"),
    ldap_search_dn: str = typer.Option(None, "--search-dn"),
    ldap_search_password: str = typer.Option(None, "--search-password"),
    ldap_base_dn: str = typer.Option(None, "--base-dn"),
    ldap_filter: str = typer.Option(None, "--filter"),
    ldap_uid: str = typer.Option(None, "--uid"),
    ldap_scope: int = typer.Option(None, "--scope"),
    ldap_connection_timeout: int = typer.Option(None, "--timeout"),
    ldap_verify_cert: bool = typer.Option(None, "--verify-cert"),
) -> None:
    """Ping LDAP service. Uses default configuration if none is provided."""
    params = model_params_from_ctx(ctx, LdapConf)
    if params:
        conf = LdapConf(**params)
    else:
        conf = None
    ldap_info = state.run(state.client.ping_ldap(conf))
    render_result(ldap_info, ctx)


# FIXME: this will never return more than one user...
#        Should we rename to `user` and return an LdapUser instead
#        of a list (len=1) of LdapUser?
@search_cmd.command("users")
def search_users(
    ctx: typer.Context,
    username: str = typer.Argument(..., help="Username to search for"),
) -> None:
    """Search for users in LDAP."""
    result = state.run(state.client.search_ldap_users(username))
    render_result(result, ctx)


@search_cmd.command("groups")
def search_groups(
    ctx: typer.Context,
    group_name: Optional[str] = typer.Option(None, help="Group name to search for"),
    group_dn: Optional[str] = typer.Option(None, help="Group DN to search for"),
) -> None:
    """Search for groups in LDAP."""
    if not group_name and not group_dn:
        raise typer.BadParameter("One of --group-name or --group-dn is required")
    result = state.run(state.client.search_ldap_groups(group_name, group_dn))
    render_result(result, ctx)
