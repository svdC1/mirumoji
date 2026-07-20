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
        panel_sync (dict[int, Callable[[], None]]): Per-panel refresh
            callbacks, keyed by navigation index, that re-read the managed
            user configuration into the panel's display elements whenever the
            main page shows it again
    """

    notify: Callable[[str, str], None]
    set_busy: Callable[[bool], None]
    backend: Backend = Backend.MODAL
    source: ImageSource = ImageSource.PULL
    env_path: Path = HOST_CONFIG_FILE
    env: dict[str, str] = field(default_factory=dict)
    busy: bool = False
    panel_sync: dict[int, Callable[[], None]] = field(default_factory=dict)

    def register_sync(self, index: int, refresh: Callable[[], None]) -> None:
        """
        Registers a panel's refresh callback under its navigation index

        A panel is built once and then cached, so anything it renders from the
        managed configuration goes stale as soon as another panel changes it.
        Registering here is what makes the main page refresh it on every visit

        Args:
            index (int): The panel's navigation index
            refresh (Callable[[], None]): Re-reads the configuration into the
                panel's display elements
        """
        self.panel_sync[index] = refresh

    def sync_panel(self, index: int) -> None:
        """
        Runs a panel's refresh callback, if it registered one

        Args:
            index (int): The panel's navigation index
        """
        refresh = self.panel_sync.get(index)
        if refresh is not None:
            refresh()

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
