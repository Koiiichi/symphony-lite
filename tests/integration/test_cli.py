import pytest

typer = pytest.importorskip("typer")
from typer.testing import CliRunner

import cli

runner = CliRunner()
command = typer.main.get_command(cli.main)


def test_cli_dry_run(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<html></html>")

    result = runner.invoke(command, ["--project", str(project), "--dry-run", "Improve spacing"])

    assert result.exit_code == 0
    assert "Status: dry_run" in result.stdout


def test_cli_creates_missing_dir(tmp_path):
    project = tmp_path / "new-app"
    result = runner.invoke(
        command,
        ["--project", str(project), "--dry-run", "Create a landing page"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert project.exists()
