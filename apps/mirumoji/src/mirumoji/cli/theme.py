"""
Defines the Rich Theme + Consoles for the CLI

Maps the frontend's "Sumi & Shu" design to `Rich` styles so that the terminal
output matches the frontend. Defines a shared `console` for output and
a `err_console` for errors
"""

from rich.console import Console
from rich.theme import Theme

# Frontend "Sumi & Shu" Design (truecolor hex)
MIRUMOJI_THEME = Theme(
    {
        "accent": "#E2533B",  # shu -> primary actions, active state
        "accent.soft": "#F08A6E",  # shu-soft -> hover
        "info": "#5E83A4",  # links, info
        "success": "#8AA06A",  # matcha green
        "danger": "bold #C8503D",
        "warning": "#D9A441",
        "muted": "#7E7567",  # ink-faint -> streamed output, hints
        "heading": "bold #F4EEE3",  # ink
        "ink": "#F4EEE3",
    }
)

console = Console(theme=MIRUMOJI_THEME, highlight=False)
err_console = Console(theme=MIRUMOJI_THEME, stderr=True, highlight=False)
