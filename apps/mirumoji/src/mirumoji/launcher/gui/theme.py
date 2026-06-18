"""
Defines the "Sumi & Shu" theme for the Flet GUI

Exposes a color palette, a Material `ft.Theme` + Font Registration, and themed
subclasses for flet primitives

info: Fontend + CLI Design
    - Warm Sumi-Ink Surfaces
    - Washi Text
    - Single Vermilion (shu) Accent
"""

from collections.abc import Callable
from typing import Any

import flet as ft

from ..core.docker_progress import classify
from ..core.log_render import tokenize

# --- Color Palette ---

BG = "#15120F"  # app background
SURFACE = "#201B16"  # cards / sidebar
SURFACE_2 = "#2A241D"  # inputs / insets
BORDER = "#3A332B"  # hairline borders
INK = "#F4EEE3"  # primary text
INK_MUTED = "#B7AD9C"  # secondary text
INK_FAINT = "#7E7567"  # hints / streamed output
SHU = "#E2533B"  # primary actions, active state
SHU_SOFT = "#F08A6E"  # hover
AI = "#5E83A4"  # info
MATCHA = "#8AA06A"  # success
DANGER = "#C8503D"  # errors
WARNING = "#D9A441"  # warnings

# --- Typography ---

DISPLAY = "Newsreader"  # headings + wordmark
BODY = "Hanken Grotesk"  # UI / body
MONO = "JetBrains Mono"  # streamed command output

FONT_FILES: dict[str, str] = {
    DISPLAY: "fonts/Newsreader.ttf",
    BODY: "fonts/HankenGrotesk.ttf",
    MONO: "fonts/JetBrainsMono.ttf",
}

# --- Spacing /Shape ---

RADIUS = 12
GAP = 16
PAD = 22

# --- Constants ---


# Cap the live log so long streams don't grow the control unbounded.
# The buffer is allowed to overshoot the cap by one batch, then the oldest
# block is removed at once
_MAX_LOG_LINES = 800
_CULL_BATCH = 100

_STATUS_COLORS: dict[str, str] = {
    "success": MATCHA,
    "danger": DANGER,
    "warning": WARNING,
    "info": AI,
    "muted": INK_FAINT,
}

# Maps a Docker progress `kind` (see `core.docker_progress`) to a palette
# colour
_KIND_COLORS: dict[str, str] = {
    "done": MATCHA,
    "active": AI,
    "idle": INK_FAINT,
    "free": INK,
}

# Maps a log-segment `kind` (see `core.log_render`) to a palette colour. The
# `level` kind is coloured by the level word via `_LEVEL_COLORS` instead
_LOG_KIND_COLORS: dict[str, str] = {
    "service": SHU,
    "uuid": SHU_SOFT,
    "url": AI,
    "path": AI,
    "number": "#C99A57",
    "ok": MATCHA,
    "bad": DANGER,
    "warn": WARNING,
    "plain": INK,
}

_LEVEL_COLORS: dict[str, str] = {
    "DEBUG": INK_FAINT,
    "INFO": AI,
    "WARNING": WARNING,
    "ERROR": DANGER,
    "CRITICAL": DANGER,
}

# --- Global Theme ---


def MirumojiTheme() -> ft.Theme:
    """
    Builds the GUI's global theme

    Defines a `ft.ColorScheme` based on the `Sumi & Shu Color Palette`

    info: Fonts
        - Uses the `Hanken Grotesk` font for main UI + body text

        - Uses `Newsreader` for headlines and labels

    Returns:
        The configured `ft.Theme` object
    """
    return ft.Theme(
        font_family=BODY,
        color_scheme=ft.ColorScheme(
            primary=SHU,
            on_primary=INK,
            secondary=AI,
            on_secondary=INK,
            surface=SURFACE,
            on_surface=INK,
            error=DANGER,
            on_error=INK,
            outline=BORDER,
        ),
        # Globally style all text variants
        text_theme=ft.TextTheme(
            # Heading
            headline_large=ft.TextStyle(
                size=30,
                weight=ft.FontWeight.BOLD,
                color=INK,
                font_family=DISPLAY,
            ),
            # Body
            body_medium=ft.TextStyle(
                size=14,
                color=INK_MUTED,
                font_family=BODY,
            ),
            # Label
            label_small=ft.TextStyle(
                size=11,
                weight=ft.FontWeight.W_600,
                color=INK_FAINT,
                font_family=DISPLAY,
            ),
        ),
        # CheckBoxes
        checkbox_theme=ft.CheckboxTheme(
            fill_color={
                ft.ControlState.SELECTED: SHU,
                ft.ControlState.DEFAULT: "transparent",
            },
            check_color=INK,
            splash_radius=0,
        ),
    )


# --- Custom Primitives ---

# --- Progress ---


class ButtonProgressRing(ft.ProgressRing):
    """
    Builds a small leading progress ring to be shown while a button is loading

    Args:
        color (str): The ring colour
    """

    def __init__(self, color: str, **kwargs: Any) -> None:
        super().__init__(
            width=16,
            height=16,
            color=color,
            stroke_width=2,
            **kwargs,
        )


# --- Buttons ---


class PrimaryActionButton(ft.ElevatedButton):
    """
    A primary (shu) action button that can swap to a loading spinner
    """

    def __init__(
        self,
        text: str,
        *,
        on_click: Callable[[Any], Any] | None = None,
        icon: ft.IconData | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            content=text,
            on_click=on_click,
            icon=icon,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=18, vertical=18),
                bgcolor={
                    ft.ControlState.DEFAULT: SHU,
                    ft.ControlState.DISABLED: SURFACE_2,
                },
                color={
                    ft.ControlState.DEFAULT: INK,
                    ft.ControlState.DISABLED: INK_FAINT,
                },
            ),
            **kwargs,
        )
        self._icon = icon

    def set_loading(self, is_loading: bool) -> None:
        """
        Toggles a leading spinner without changing the button's footprint

        Only the leading icon is swapped for a progress ring (the label is
        kept), so the button keeps its shape; it is disabled while loading to
        prevent double-clicks

        Args:
            is_loading (bool): Whether to show the spinner
        """
        self.disabled = is_loading
        self.icon = ButtonProgressRing(INK) if is_loading else self._icon
        self.update()


class SecondaryActionButton(ft.OutlinedButton):
    """
    A secondary (outlined) action button that can swap to a loading spinner
    """

    def __init__(
        self,
        text: str,
        *,
        on_click: Callable[[Any], Any] | None = None,
        icon: ft.IconData | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            content=text,
            on_click=on_click,
            icon=icon,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=16, vertical=18),
                color={
                    ft.ControlState.DEFAULT: INK,
                    ft.ControlState.DISABLED: INK_FAINT,
                },
                side={
                    ft.ControlState.DEFAULT: ft.BorderSide(1, BORDER),
                    ft.ControlState.DISABLED: ft.BorderSide(1, "transparent"),
                },
                bgcolor={ft.ControlState.DISABLED: SURFACE_2},
            ),
            **kwargs,
        )
        self._icon = icon

    def set_loading(self, is_loading: bool) -> None:
        """
        Toggles a leading spinner without changing the button's footprint

        Only the leading icon is swapped for a progress ring (the label is
        kept), so the button keeps its shape; it is disabled while loading to
        prevent double-clicks

        Args:
            is_loading (bool): Whether to show the spinner
        """
        self.disabled = is_loading
        self.icon = ButtonProgressRing(INK_FAINT) if is_loading else self._icon
        self.update()


class HelpIcon(ft.IconButton):
    """
    Builds a faint `?` icon that reveals `text` as a hover tooltip

    Args:
        text (str): The tooltip text (typically a long field description)
    """

    def __init__(self, text: str, **kwargs: Any):
        super().__init__(
            icon=ft.Icons.HELP_OUTLINE,
            tooltip=text,
            icon_color=INK_FAINT,
            icon_size=18,
            **kwargs,
        )


# --- Containers ---


class SurfaceCardContainer(ft.Container):
    """
    Wraps content in a surface card with a hairline border

    Inherits from `ft.Container`, exposing all of its arguments
    """

    def __init__(
        self,
        content: ft.Control,
        padding: int = PAD,
        **kwargs: Any,
    ):
        super().__init__(
            content=content,
            bgcolor=SURFACE,
            padding=padding,
            border_radius=RADIUS,
            border=ft.Border.all(1, BORDER),
            **kwargs,
        )


# --- Custom Components (Bundled Layout Objects) ---


# --- Shared ---


class TerminalSurface(ft.Container):
    """
    The shared output surface for streamed command output

    Inherits from `ft.Container` and exposes all of its arguments

    info: Layout
        - Shows a monospace log list inside a bordered card with a status
          header

        - A header button clears the log list, leaving the status and any
          running operation untouched

        - A header toggle hides the log list (preserving its contents) and
          shrinks the card to its header bar.Toggling again restores it

        - In-progress status is shown in the header

        - final success / error outcomes are surfaced as toasts by the actions
          that drive the surface

    Attributes:
        list_view (ft.ListView): The scrolling, monospace log list
        status_text (ft.Text): The colour-coded header status label
        copy_button (ft.IconButton): Copies the buffered output to the
            clipboard
        clear_button (ft.IconButton): Clears the log list
        logs_toggle (ft.IconButton): Hides / shows the log list
    """

    def __init__(self, *, log_view: bool = False, **kwargs: Any) -> None:
        # When `log_view`, free lines are tokenized and themed like the server
        # console instead of the dimmed `key  value` split
        self._log_view = log_view
        # Highlight the docker service prefix only when logs are unfiltered
        self.with_service = True
        # Log list (kept in memory so that logs aren't lost while collapsed)
        self.list_view = ft.ListView(
            expand=True,
            spacing=6,
            auto_scroll=True,
            padding=20,
        )
        # Raw text of each shown line, kept parallel to `list_view.controls`
        # so the whole buffer can be copied to the clipboard
        self._lines: list[str] = []
        # Docker layer id -> its in-place row, so per-layer progress updates
        # overwrite one row instead of appending a line on every update
        self._layer_rows: dict[str, ft.Text] = {}

        self.status_text = ft.Text(
            "Ready",
            color=INK_FAINT,
            size=12,
            weight=ft.FontWeight.BOLD,
        )
        self._output_label = ft.Text(
            "OUTPUT",
            size=11,
            weight=ft.FontWeight.W_600,
            color=INK_FAINT,
        )
        self.copy_button = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY,
            tooltip="Copy Output",
            icon_size=18,
            icon_color=INK_FAINT,
            on_click=self._copy_logs,
        )
        self.clear_button = ft.IconButton(
            icon=ft.Icons.CLEAR_ALL,
            tooltip="Clear Output",
            icon_size=18,
            icon_color=INK_FAINT,
            on_click=self._clear_logs,
        )
        self.logs_toggle = ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            tooltip="Hide Logs",
            icon_size=18,
            icon_color=INK_FAINT,
            on_click=self._toggle_logs,
        )

        self._header = ft.Container(
            content=ft.Row(
                [
                    self._output_label,
                    ft.Container(expand=True),  # Spacer
                    self.status_text,
                    self.copy_button,
                    self.clear_button,
                    self.logs_toggle,
                ],
            ),
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            bgcolor=SURFACE,
            border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
        )

        super().__init__(
            content=ft.Column([self._header, self.list_view], spacing=0),
            bgcolor=BG,
            border=ft.Border.all(1, BORDER),
            border_radius=RADIUS,
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            **kwargs,
        )

    def _repaint(self) -> None:
        """
        Repaints the surface, but only while it is mounted

        Updating a control detached from the page (e.g. after navigating to
        another panel mid-stream) raises, so guard on `self.page`
        """
        if self.page is not None:
            self.update()

    def _set_collapsed(self, collapsed: bool) -> None:
        """
        Hides or shows the log list, preserving its contents

        When `collapsed` is `True`, the log list is hidden and the card
        shrinks to its header bar. The buffered log lines are kept in memory
        and reappear when expanded again

        Args:
            collapsed (bool): Whether to hide the log list
        """
        self.list_view.visible = not collapsed
        self.expand = not collapsed
        self.logs_toggle.icon = (
            ft.Icons.VISIBILITY if collapsed else ft.Icons.VISIBILITY_OFF
        )
        self.logs_toggle.tooltip = "Show Logs" if collapsed else "Hide Logs"
        self._repaint()

    def _toggle_logs(self, e: ft.Event[ft.IconButton]) -> None:
        """
        Toggles the log list between shown and hidden

        Args:
            e (ft.Event[ft.IconButton]): The toggle click event
        """
        self._set_collapsed(self.list_view.visible)

    def _clear_logs(self, e: ft.Event[ft.IconButton]) -> None:
        """
        Clears the log list from the header button, keeping the status

        Args:
            e (ft.Event[ft.IconButton]): The clear click event
        """
        self.clear()
        self._repaint()

    async def _copy_logs(self, e: ft.Event[ft.IconButton]) -> None:
        """
        Copies the full buffered output to the system clipboard

        Args:
            e (ft.Event[ft.IconButton]): The copy click event
        """
        text = "\n".join(self._lines)
        if not text:
            return
        await ft.Clipboard().set(text)

    def set_status(self, text: str, kind: str = "muted") -> None:
        """
        Updates the colour-coded header status label

        Args:
            text (str): The status message
            kind (str): A key fromt the status palette (success / danger /
                warning / info / muted)
        """
        self.status_text.value = text.upper()
        self.status_text.color = _STATUS_COLORS.get(kind, INK_FAINT)
        self._repaint()

    def _row_index(self, row: ft.Text) -> int | None:
        """
        Finds a row's position in the log list by identity

        Args:
            row (ft.Text): The control to locate

        Returns:
            Its index in `list_view.controls`, or `None` when it is absent
        """
        for index, control in enumerate(self.list_view.controls):
            if control is row:
                return index
        return None

    def _log_spans(self, text: str) -> list[ft.TextSpan]:
        """
        Builds themed spans for a container log line

        Args:
            text (str): The raw log line

        Returns:
            One `ft.TextSpan` per tokenized segment, coloured like the server
            console (the service prefix is highlighted only when unfiltered)
        """
        spans: list[ft.TextSpan] = []
        for segment, kind in tokenize(text, with_service=self.with_service):
            if kind == "level":
                color = _LEVEL_COLORS.get(segment, INK)
            else:
                color = _LOG_KIND_COLORS.get(kind, INK)
            spans.append(ft.TextSpan(segment, ft.TextStyle(color=color)))
        return spans

    def append_log(self, text: str) -> None:
        """
        Renders one monospace output line

        Docker per-layer progress lines are collapsed by layer id, overwriting
        a single in-place row coloured by status, so a `pull` reads like a
        console instead of a flood of per-update lines. Every other line is
        appended as usual, with a leading ``key  ↦`` column dimmed

        Args:
            text (str): The output line to render
        """
        kind, layer_id = classify(text)

        # Collapse a known Docker layer into its existing in-place row
        if layer_id is not None and layer_id in self._layer_rows:
            color = _KIND_COLORS.get(kind, INK)
            row = self._layer_rows[layer_id]
            row.spans = [ft.TextSpan(text, ft.TextStyle(color=color))]
            index = self._row_index(row)
            if index is not None:
                self._lines[index] = text
            return

        # Otherwise build a new row: a single coloured span for Docker
        # progress, or the dimmed `key  value` split for any other line
        if layer_id is not None:
            color = _KIND_COLORS.get(kind, INK)
            spans = [ft.TextSpan(text, ft.TextStyle(color=color))]
        elif self._log_view:
            spans = self._log_spans(text)
        else:
            parts = text.split("  ", 2)
            if len(parts) >= 2:
                spans = [
                    ft.TextSpan(
                        f"{parts[0]}  ",
                        ft.TextStyle(color=INK_FAINT),
                    ),
                    ft.TextSpan("  ".join(parts[1:]), ft.TextStyle(color=INK)),
                ]
            else:
                spans = [ft.TextSpan(text, ft.TextStyle(color=INK))]

        row = ft.Text(spans=spans, size=13, font_family=MONO, selectable=True)
        if layer_id is not None:
            self._layer_rows[layer_id] = row
        self.list_view.controls.append(row)
        self._lines.append(text)

        # Batch-Removal -> Dropping the oldest line on every append is O(n) per
        # line. Instead, let the buffer overshoot, then trim a block at once so
        # the expensive shift happens once per `_CULL_BATCH` lines. Drop any
        # collapsed layer rows that fall out of the window with it
        if len(self.list_view.controls) >= _MAX_LOG_LINES + _CULL_BATCH:
            culled = {id(c) for c in self.list_view.controls[:_CULL_BATCH]}
            del self.list_view.controls[:_CULL_BATCH]
            del self._lines[:_CULL_BATCH]
            self._layer_rows = {
                lid: row
                for lid, row in self._layer_rows.items()
                if id(row) not in culled
            }

    def clear(self) -> None:
        """
        Clears all current log lines
        """
        self.list_view.controls.clear()
        self._lines.clear()
        self._layer_rows.clear()


class NotificationBar(ft.SnackBar):
    """
    A floating, globally styled toast notification
    """

    def __init__(self, message: str, kind: str = "info", **kwargs: Any):
        accent_color = _STATUS_COLORS.get(kind, INK_FAINT)

        super().__init__(
            content=ft.Text(
                message,
                color=INK,
                weight=ft.FontWeight.W_500,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=SURFACE_2,
            behavior=ft.SnackBarBehavior.FLOATING,
            # Fixed width keeps the toast a centered pill
            # Wide enough for one-line messages without spanning the whole
            # window. SnackBars are always bottom-anchored
            width=640,
            duration=4000,
            show_close_icon=True,
            close_icon_color=INK_MUTED,
            shape=ft.RoundedRectangleBorder(
                radius=RADIUS, side=ft.BorderSide(2, accent_color)
            ),
            **kwargs,
        )


def StatusPill(text: str, kind: str = "muted", **kwargs: Any) -> ft.Container:
    """
    A rounded, tinted status chip built from an `ft.Container`

    Args:
        text (str): The chip's label
        kind (str): A key fromt the status palette (success / danger / warning
            / info / muted)
        **kwargs (Any): Additional arguments for the underlying `ft.Container`

    Returns:
        The configured `ft.Container`
    """
    color = _STATUS_COLORS.get(kind, INK_FAINT)
    return ft.Container(
        content=ft.Text(
            text,
            size=12,
            color=color,
            weight=ft.FontWeight.W_600,
        ),
        bgcolor=ft.Colors.with_opacity(0.14, color),
        padding=ft.Padding.symmetric(horizontal=12, vertical=5),
        border_radius=999,
        **kwargs,
    )


class Section(SurfaceCardContainer):
    """
    Builds a `SurfaceCardContainer` (`ft.Container`) with a custom
    `ft.Column` as its content to be used as a section

    Forwards all kwargs to the underlying `ft.Container`
    """

    def __init__(
        self,
        title: str,
        *controls: ft.Control,
        subtitle: str | None = None,
        **kwargs: Any,
    ):
        header: list[ft.Control] = [
            ft.Text(
                title.upper(),
                theme_style=ft.TextThemeStyle.LABEL_SMALL,
            ),
        ]

        if subtitle is not None:
            header.append(
                ft.Text(
                    subtitle,
                    size=12,
                    color=INK_MUTED,
                )
            )

        header.append(ft.Divider(height=9, color=BORDER))

        content_column = ft.Column(
            [*header, *controls],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        super().__init__(content=content_column, **kwargs)


# --- Settings ---


class SettingsDropdown(ft.Column):
    """
    A themed dropdown field following the same open layout as `SettingsInput`

    Inherits from `ft.Column` and exposes all of its arguments
    """

    def __init__(
        self,
        label_text: str,
        value: str,
        options: list[str],
        **kwargs: Any,
    ):
        self.dropdown = ft.Dropdown(
            value=value,
            color=INK,
            bgcolor=SURFACE_2,
            border_color="transparent",
            focused_border_color=SHU,
            border=ft.InputBorder.UNDERLINE,
            border_width=2,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=16),
            options=[ft.dropdown.Option(opt) for opt in options],
            **kwargs,
        )

        super().__init__(
            spacing=4,
            controls=[
                ft.Text(
                    label_text.upper(),
                    theme_style=ft.TextThemeStyle.LABEL_SMALL,
                ),
                self.dropdown,
            ],
        )


class SettingsInput(ft.Column):
    """
    A labelled, full-width text input

    Inherits from `ft.Column` and exposes all of its arguments

    The label sits above a full-width field. An optional `description` is shown
    as a `?` hover tooltip beside the label, and an optional `helper` line can
    sit below the field

    Attributes:
        field (ft.TextField): The underlying text field
    """

    def __init__(
        self,
        label_text: str,
        value: str = "",
        description: str | None = None,
        helper: str | None = None,
        password: bool = False,
        **kwargs: Any,
    ) -> None:
        self.field = ft.TextField(
            value=value,
            password=password,
            can_reveal_password=password,
            color=INK,
            bgcolor=SURFACE_2,
            border_color="transparent",
            focused_border_color=SHU,
            border=ft.InputBorder.UNDERLINE,
            border_width=2,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=16),
            text_size=14,
            **kwargs,
        )

        label: ft.Control = ft.Text(
            label_text.upper(), theme_style=ft.TextThemeStyle.LABEL_SMALL
        )
        if description:
            label = ft.Row(
                [label, HelpIcon(description)],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        controls: list[ft.Control] = [label, self.field]
        if helper:
            controls.append(ft.Text(helper, size=11, color=INK_FAINT))

        # STRETCH so that the field fills the input's width
        super().__init__(
            spacing=4,
            controls=controls,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
