"""
Defines a minimal Flet shell for the Mirumoji GUI

This is the scaffold for the desktop launcher: it adopts the frontend's
"Sumi & Shu" palette and drives the same `mirumoji.cli.shared` core the CLI
uses. The full themed orchestration UI is built in the following commit
"""

from __future__ import annotations

from ..shared import checks
from ..shared.models import CheckResult, CheckStatus

# Sumi & Shu palette (matches the frontend + CLI theme)
_BG = "#15120F"
_SURFACE = "#201B16"
_INK = "#F4EEE3"
_MUTED = "#7E7567"
_SHU = "#E2533B"
_MATCHA = "#8AA06A"
_DANGER = "#C8503D"

_STATUS_COLOR = {
    CheckStatus.OK: _MATCHA,
    CheckStatus.MISSING: _DANGER,
    CheckStatus.SKIPPED: _MUTED,
}


def _all_checks() -> list[CheckResult]:
    """
    Runs every environment check for display

    Returns:
        The ordered check results
    """
    return [
        checks.docker(),
        checks.docker_compose(),
        checks.git(),
        checks.nvidia_gpu(),
        checks.nvidia_toolkit(),
        checks.flet(),
        checks.flutter(),
    ]


def main() -> None:
    """
    Launches the Flet desktop window

    Raises:
        ModuleNotFoundError: If the `gui` extra (Flet) is not installed
    """
    import flet as ft

    def view(page: ft.Page) -> None:
        page.title = "Mirumoji"
        page.bgcolor = _BG
        page.padding = 32

        results = ft.Column(spacing=8)

        def refresh(_: object = None) -> None:
            results.controls = [
                ft.Row(
                    [
                        ft.Text(
                            r.name,
                            color=_INK,
                            width=220,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            r.detail or r.status.value.title(),
                            color=_STATUS_COLOR[r.status],
                        ),
                    ],
                )
                for r in _all_checks()
            ]
            page.update()

        page.add(
            ft.Text(
                "Mirumoji",
                size=32,
                color=_INK,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                "Self-Hostable Japanese Immersion Toolkit",
                color=_MUTED,
            ),
            ft.Container(height=16),
            ft.ElevatedButton(
                "Check Environment",
                bgcolor=_SHU,
                color=_INK,
                on_click=refresh,
            ),
            ft.Container(height=16),
            ft.Container(
                content=results,
                bgcolor=_SURFACE,
                padding=20,
                border_radius=10,
            ),
        )
        refresh()

    ft.app(target=view)  # type: ignore[no-untyped-call]
