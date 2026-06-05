"""
Defines the `Mirumoji` CLI application built with `Typer` and `Rich`

This is the single entry point for the package (`mirumoji`)
"""

import typer

from .commands import (
    build,
    doctor,
    down,
    gui,
    logs,
    pull,
    render,
    server,
    status,
    up,
)

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Mirumoji — Self-Hostable Japanese Immersion Toolkit",
)

app.command("up")(up)
app.command("down")(down)
app.command("status")(status)
app.command("logs")(logs)
app.command("build")(build)
app.command("pull")(pull)
app.command("doctor")(doctor)
app.command("server")(server)
app.command("gui")(gui)
app.command("render")(render)


if __name__ == "__main__":
    app()
