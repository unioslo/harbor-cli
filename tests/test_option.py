from __future__ import annotations

from harbor_cli.config import env_var
from harbor_cli.option import Option
from harbor_cli.style import help_config_override


def test_option() -> None:
    base_help = "Base help text."
    default = "default"
    info = Option(
        default,
        "--option",
        "-o",
        help=base_help,
        envvar=env_var("OPTION"),
        config_override="option",
    )

    # The help text should be updated with the config override info
    assert info.help == base_help + " " + help_config_override("option")
    assert info._help_original == base_help
    assert info.config_override == "option"
    # Test the rest of the attributes
    assert info.envvar == env_var("OPTION")
    assert info.param_decls == ("--option", "-o")
    assert info.default == default


def test_option_no_config_override() -> None:
    info = Option("default", "--option", "-o", help="Help text.")

    # The help text should be updated with the config override info
    assert info.help == "Help text."
    assert info._help_original == info.help
    # Test the rest of the attributes
    assert info.param_decls == ("--option", "-o")
    assert info.default == "default"


def test_option_no_help() -> None:
    info = Option("default", "--option", "-o")

    # The help text should be updated with the config override info
    assert info.help is None
    assert info._help_original is None
    # Test the rest of the attributes
    assert info.param_decls == ("--option", "-o")
    assert info.default == "default"
