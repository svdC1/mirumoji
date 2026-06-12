"""
Defines a mutable cross-panel state for the GUI

tip: Usage
    - Stores the user's configuration so that the UI doesn't have to re-load
      the `.env` on every panel

    - Holds the UI's internal state, such as whether or not an action is
      happening (`busy`)

    - Holds objects that should be accessible from any panel, such
      as the callback function to display a toast notification
      on the application-scoped `NotificationBar` (`notify`)
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from ...paths import HOST_CONFIG_FILE
from ..core import envfile
from ..core.models import Backend, ImageSource


@dataclass
class AppState:
    """
    The GUI's Current Working State

    Attributes:
        notify (Callable[[str, str], None]): The callback function attached to
            the application-scoped `NotificationBar` that triggers the display
            of a toast notification when called
        set_busy (Callable[[bool], None]): The callback function that
            locks/unlocks the navigation and panel buttons while a long-running
            action is in progress to prevent the user from changing
            the configuration or navigating away mid-action
        backend (Backend): The chosen mirumoji transcription backend
        source (ImageSource): Whether to pull pre-built images or build locally
        env_path (Path): Path to the managed user configuration file (`.env`)
        env (dict[str, str]): Resolved environment variables (from `env_path`)
        busy (bool): Whether a long-running action is in progress
        sync_dashboard (Callable[[], None] | None): The callback function
            attached to the dashboard's configuration-display elements that
            updates the shown configuration based on the managed user
            configuration file whenver the dashboard is re-loaded by the main
            page
    """

    notify: Callable[[str, str], None]
    set_busy: Callable[[bool], None]
    backend: Backend = Backend.MODAL
    source: ImageSource = ImageSource.PULL
    env_path: Path = HOST_CONFIG_FILE
    env: dict[str, str] = field(default_factory=dict)
    busy: bool = False
    sync_dashboard: Callable[[], None] | None = None

    def load_deployment(self, env: Mapping[str, str]) -> None:
        """
        Adopts the persisted backend / image-source choice from `env`

        Values that are missing or unrecognised leave the current selection
        unchanged

        Args:
            env (Mapping[str, str]): The resolved environment values
        """
        backend, source = envfile.read_deployment(env)
        if backend is not None:
            self.backend = backend
        if source is not None:
            self.source = source
