"""
Defines the `Mirumoji` CLI application built with `Typer` and `Rich`

This is the single entry point for the package (`mirumoji`)
"""

import typer

from ...log import setup_logging
from .commands import (
    build,
    config_clear,
    config_delete,
    config_import,
    config_path,
    config_set,
    config_show,
    dev_server,
    dev_up,
    doctor,
    down,
    gui,
    logs,
    modal_deploy,
    modal_down,
    modal_download_data,
    modal_status,
    pull,
    render,
    reset,
    status,
    up,
)

app = typer.Typer(
    name="mirumoji",
    no_args_is_help=True,
    add_completion=False,
    help="Mirumoji • Self-Hostable Japanese Immersion Toolkit",
)


@app.callback()
def _configure() -> None:
    """
    Routes launcher logs to `launcher.log` before any command runs

    info: Console Off
        The console handler is disabled so diagnostic records never mix into a
        command's `Rich` output, which is the launcher's user-facing surface
    """
    setup_logging(log_file="launcher.log", console=False)


app.command("up")(up)
app.command("down")(down)
app.command("reset")(reset)
app.command("status")(status)
app.command("logs")(logs)
app.command("build")(build)
app.command("pull")(pull)
app.command("doctor")(doctor)
app.command("gui")(gui)
app.command("render")(render)

# Config Management Subcommands (`mirumoji config ...`)
config_app = typer.Typer(
    no_args_is_help=True,
    help="Manage The Launcher's Configuration (.env)",
)
config_app.command("set")(config_set)
config_app.command("delete")(config_delete)
config_app.command("import")(config_import)
config_app.command("show")(config_show)
config_app.command("path")(config_path)
config_app.command("clear")(config_clear)
app.add_typer(config_app, name="config")

# Development Only Subcommands (`mirumoji dev ...`)
dev_app = typer.Typer(
    no_args_is_help=True,
    help="Development-Only Commands For The Mirumoji Package",
)
dev_app.command("server")(dev_server)
dev_app.command("up")(dev_up)
app.add_typer(dev_app, name="dev")

# Modal Host Subcommands (`mirumoji modal ...`)
modal_app = typer.Typer(
    no_args_is_help=True,
    help="Deploy And Manage The Modal-Hosted Mirumoji App",
)
modal_app.command("deploy")(modal_deploy)
modal_app.command("status")(modal_status)
modal_app.command("down")(modal_down)
modal_app.command("download-data")(modal_download_data)
app.add_typer(modal_app, name="modal")


if __name__ == "__main__":
    app()
