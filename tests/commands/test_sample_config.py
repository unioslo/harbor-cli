from __future__ import annotations

from typer.testing import CliRunner

from harbor_cli.main import app

runner = CliRunner()


def test_app():
    result = runner.invoke(app, ["sample-config"])
    assert result.exit_code == 0
