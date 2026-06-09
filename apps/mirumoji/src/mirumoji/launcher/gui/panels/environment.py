"""
Defines the Environment panel (the GUI equivalent of `mirumoji doctor`)

Runs every dependency check off the UI thread and renders the results as a
status table
"""

import flet as ft

from ...core import checks
from ...core.models import CheckResult, CheckStatus
from .. import theme
from ..runner import run_blocking
from ..state import AppState

_STATUS_KIND = {
    CheckStatus.OK: "success",
    CheckStatus.MISSING: "danger",
    CheckStatus.SKIPPED: "muted",
}


def _all_checks() -> list[CheckResult]:
    """
    Runs every dependency check

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


def _row(result: CheckResult) -> ft.Control:
    """
    Builds a single check result row

    Args:
        result (CheckResult): The check result to render

    Returns:
        The row control
    """
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=11, horizontal=2),
        content=ft.Row(
            controls=[
                ft.Text(
                    result.name,
                    color=theme.INK,
                    width=210,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Text(
                    result.detail or "—",
                    color=theme.INK_MUTED,
                    size=13,
                    expand=True,
                ),
                theme.StatusPill(
                    result.status.value.title(),
                    _STATUS_KIND[result.status],
                ),
            ],
        ),
    )


def _rows(items: list[CheckResult]) -> list[ft.Control]:
    """
    Interleaves result rows with hairline dividers

    Args:
        items (list[CheckResult]): The results to render

    Returns:
        The row + divider controls
    """
    out: list[ft.Control] = []
    for i, item in enumerate(items):
        if i:
            out.append(ft.Divider(height=1, color=theme.BORDER))
        out.append(_row(item))
    return out


def build(page: ft.Page, state: AppState) -> ft.Control:
    """
    Builds the Environment panel

    Args:
        page (ft.Page): The owning page (for background work + updates)
        state (AppState): The shared GUI state (used for toast notifications)

    Returns:
        The panel's root control
    """
    results = ft.Column(spacing=0)
    run_btn = theme.PrimaryActionButton(
        "Run Checks", on_click=lambda _: refresh(), icon=ft.Icons.PLAY_ARROW
    )

    # Hidden until there are results, so that no empty surface shows on first
    # load
    results_card = theme.Section("Dependencies", results)
    results_card.visible = False

    def render(items: list[CheckResult]) -> None:
        results.controls = _rows(items)
        results_card.visible = True
        run_btn.set_loading(False)
        page.update()

    def fail(exc: Exception) -> None:
        run_btn.set_loading(False)
        page.update()
        state.notify(f"Checks Failed  ↦  {exc}", "danger")

    def refresh() -> None:
        run_btn.set_loading(True)
        results.controls = []
        page.update()
        run_blocking(page, _all_checks, render, on_error=fail)

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=theme.GAP,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Text(
                "Environment",
                theme_style=ft.TextThemeStyle.HEADLINE_LARGE,
            ),
            ft.Text(
                "External Dependencies Needed By The Launcher",
                theme_style=ft.TextThemeStyle.BODY_MEDIUM,
            ),
            ft.Container(height=4),
            ft.Row([run_btn], spacing=16),
            results_card,
        ],
    )
