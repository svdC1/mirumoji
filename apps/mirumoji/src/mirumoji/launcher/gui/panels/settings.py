"""
Defines the Settings panel

Configures the transcription backend, image source, and the environment
variables the launcher writes to the managed config file
"""

from pathlib import Path

import flet as ft

from ...core import envfile
from ...core.constants import (
    ADVANCED_VARS,
    IMAGE_SOURCE_VAR,
    LLM_VARS,
    MODAL_VARS,
    TRANSCRIBE_BACKEND_VAR,
)
from ...core.errors import EnvConfigError
from ...core.models import Backend, EnvVar, ImageSource
from .. import theme
from ..state import AppState

# A 0/1 flag, so it is rendered as a checkbox rather than a text field
_FORCE_BUILD = "MODAL_FORCE_BUILD"


def _input_fields(
    specs: tuple[EnvVar, ...],
    env: dict[str, str],
) -> tuple[list[ft.Control], dict[str, theme.SettingsInput]]:
    """
    Builds a labelled, full-width input per environment variable

    The variable name is the field label and its (often long) description is a
    `?` hover tooltip beside the label

    Args:
        specs (tuple[EnvVar, ...]): The variables to render
        env (dict[str, str]): The current resolved values

    Returns:
        The input controls and a mapping of variable name to its input
    """
    controls: list[ft.Control] = []
    fields: dict[str, theme.SettingsInput] = {}
    for var in specs:
        field = theme.SettingsInput(
            var.name,
            env.get(var.name, var.default),
            description=var.description,
            password=var.secret,
        )
        fields[var.name] = field
        controls.append(field)
    return controls, fields


def build(page: ft.Page, state: AppState) -> ft.Control:
    """
    Builds the Settings panel

    Args:
        page (ft.Page): The owning page
        state (AppState): The shared GUI state to read and update

    Returns:
        The panel's root control
    """
    # File-Only. The managed config is the single source of truth. The shell
    # environment stays a runtime override that Compose applies, so it is not
    # merged in here (which would otherwise include shell values into the file)
    state.env = envfile.read(state.env_path)

    backend_dd = theme.SettingsDropdown(
        "Transcription Backend",
        state.backend.value,
        [b.value for b in Backend],
        width=300,
    )
    source_dd = theme.SettingsDropdown(
        "Image Source",
        state.source.value,
        [s.value for s in ImageSource],
        width=300,
    )

    llm_inputs, llm_fields = _input_fields(LLM_VARS, state.env)
    modal_text_vars = tuple(v for v in MODAL_VARS if v.name != _FORCE_BUILD)
    modal_inputs, modal_fields = _input_fields(modal_text_vars, state.env)
    advanced_inputs, advanced_fields = _input_fields(ADVANCED_VARS, state.env)
    fields = {**llm_fields, **modal_fields, **advanced_fields}

    force_build_var = next(v for v in MODAL_VARS if v.name == _FORCE_BUILD)
    force_build_cb = ft.Checkbox(
        label=_FORCE_BUILD,
        value=state.env.get(_FORCE_BUILD, "0") == "1",
    )
    force_build_row = ft.Row(
        [force_build_cb, theme.HelpIcon(force_build_var.description)],
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    async def on_import(e: ft.Event[ft.Button]) -> None:
        files = await ft.FilePicker().pick_files(
            dialog_title="Select A Config File To Import",
            allow_multiple=False,
        )
        if not files:
            return
        source = Path(files[0].path or "")
        try:
            imported = envfile.import_file(source, state.env_path)
        except EnvConfigError as exc:
            state.notify(str(exc), "danger")
            return
        state.env = imported
        for name, field in fields.items():
            field.field.value = state.env.get(name, "")
        force_build_cb.value = state.env.get(_FORCE_BUILD, "0") == "1"
        # Adopt any persisted backend / image-source from the imported file
        state.load_deployment(state.env)
        backend_dd.dropdown.value = state.backend.value
        source_dd.dropdown.value = state.source.value
        page.update()
        state.notify(f"Imported {source.name}  ↦  Review And Save", "success")

    def save(_: ft.Event[ft.Button]) -> None:
        state.backend = Backend(
            backend_dd.dropdown.value or Backend.MODAL.value
        )
        state.source = ImageSource(
            source_dd.dropdown.value or ImageSource.PULL.value
        )
        for name, field in fields.items():
            value = (field.field.value or "").strip()
            if value:
                state.env[name] = value
            else:
                state.env.pop(name, None)
        if force_build_cb.value:
            state.env[_FORCE_BUILD] = "1"
        else:
            state.env.pop(_FORCE_BUILD, None)
        # Persist the deployment choice so it survives restarts and reaches the
        # server (the compose template reads MIRUMOJI_TRANSCRIBE_BACKEND)
        state.env[TRANSCRIBE_BACKEND_VAR] = state.backend.value
        state.env[IMAGE_SOURCE_VAR] = state.source.value
        envfile.write(state.env_path, state.env)
        state.notify(f"Saved To {state.env_path}", "success")

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=theme.GAP,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Text("Settings", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
            ft.Text(
                "Trahscription Backend, Image Source, And Environment",
                theme_style=ft.TextThemeStyle.BODY_MEDIUM,
            ),
            ft.Container(height=4),
            theme.Section(
                "Deployment",
                ft.Row([backend_dd, source_dd], spacing=16, wrap=True),
            ),
            theme.Section(
                "LLM Providers",
                *llm_inputs,
                subtitle=(
                    "All Optional  ↦  LLM Features Are Disabled If None Are "
                    "Provided"
                ),
            ),
            theme.Section(
                "Modal",
                *modal_inputs,
                force_build_row,
                subtitle="Required Only For The Modal Transcription Backend",
            ),
            theme.Section(
                "Advanced",
                *advanced_inputs,
                subtitle=(
                    "Optional Overrides  ↦  The Server Has Sensible Defaults "
                    "For These"
                ),
            ),
            ft.Row(
                [
                    theme.PrimaryActionButton(
                        "Save Configuration",
                        on_click=save,
                        icon=ft.Icons.SAVE_OUTLINED,
                    ),
                    theme.PrimaryActionButton(
                        "Load Configuration",
                        on_click=on_import,
                        icon=ft.Icons.IMPORT_EXPORT,
                    ),
                ],
                spacing=16,
            ),
        ],
    )
