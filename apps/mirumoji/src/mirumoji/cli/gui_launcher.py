"""
Launches the GUI application
"""

from flaskwebgui import FlaskUI  # type: ignore

from mirumoji.cli.gui.main import PORT, app, setup_logging


def main():
    """
    Entry point for the GUI console script.
    """
    setup_logging()
    FlaskUI(
        app=app,
        port=PORT,
        server="fastapi",
        fullscreen=False,
        width=1200,
        height=800,
    ).run()


if __name__ == "__main__":
    main()
