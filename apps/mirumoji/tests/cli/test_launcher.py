"""
Smoke test: verify the Click CLI group is importable and has the expected
commands
"""

from click.testing import CliRunner

from mirumoji.cli.launcher import cli


def test_cli_importable():
    """The CLI group can be imported without errors."""
    assert cli is not None


def test_cli_has_expected_commands():
    """Core CLI commands are registered."""
    command_names = set(cli.commands.keys())
    expected = {"launch", "shutdown", "launch-local", "build", "gui"}
    assert expected.issubset(command_names), (
        f"Missing commands: {expected - command_names}"
    )


def test_cli_help_exits_zero():
    """``mirumoji --help`` exits with code 0."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
