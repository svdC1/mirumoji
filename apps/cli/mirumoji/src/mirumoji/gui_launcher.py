"""
Launches the GUI application
"""

from mirumoji.gui.main import app, setup_logging, PORT
from flaskwebgui import FlaskUI
from multiprocessing import freeze_support


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
        height=800
    ).run()


if __name__ == "__main__":
    freeze_support()
    main()
