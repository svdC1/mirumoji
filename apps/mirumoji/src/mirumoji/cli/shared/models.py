"""
Defines plain data structures shared by the launcher core and its front-ends

These carry intent and results between the framework-agnostic `shared` core
and the presentation layers (Rich CLI, Flet GUI) without either side importing
the other
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Backend(str, Enum):
    """
    Defines all possible transcription backend options

    Attributes:
        LOCAL: Use the GPU image with `faster-whisper` running on the host
        MODAL: Use the CPU image and off-load transcription to Modal GPU
            containers
    """

    LOCAL = "local"
    MODAL = "modal"

    def __str__(self) -> str:
        """
        Renders as the plain value (e.g. `modal`) for prompts and help text

        Returns:
            The backend's string value
        """
        return self.value


class ImageSource(str, Enum):
    """
    Defines all possible image sources for the Docker Compose application's
    images

    Attributes:
        PULL: Pull the pre-built images from Docker Hub
        BUILD: Build the frontent + backend images locally from the managed
            repo checkout
    """

    PULL = "pull"
    BUILD = "build"


@dataclass(frozen=True)
class EnvVar:
    """
    Represents a single environment variable consumed by the application

    Attributes:
        name (str): The variable name
        required (bool): Whether the chosen backend needs it set
        secret (bool): Whether prompts should hide the typed value
        description (str): Human-facing description
        default (str): Default applied when the user leaves it blank
    """

    name: str
    required: bool = False
    secret: bool = False
    description: str = ""
    default: str = ""


class CheckStatus(str, Enum):
    """
    Represents the outcome of an environment check for a specific dependency

    Attributes:
        OK: The dependency is present and working
        MISSING: The dependency is absent or not functioning
        SKIPPED: The check did not apply to the current selection
    """

    OK = "ok"
    MISSING = "missing"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class CheckResult:
    """
    Represents the result an environment validation check for a specific
    system capability

    Attributes:
        name (str): The checked capability (e.g. `"Docker"`)
        status (CheckStatus): Whether it passed, failed, or was skipped
        detail (str): Extra context (version string, hint, error summary)
    """

    name: str
    status: CheckStatus
    detail: str = ""

    @property
    def ok(self) -> bool:
        """
        Whether the environment validation check passed

        Returns:
            `True` if the status is `OK`
        """
        return self.status is CheckStatus.OK


@dataclass(frozen=True)
class ComposeSpec:
    """
    Represents the fully resolved description of the stack to run

    Attributes:
        backend (Backend): The transcription backend
        source (ImageSource): Pull vs local build
        env (dict[str, str]): Resolved environment passed to compose
        project_name (str): The compose project name
    """

    backend: Backend
    source: ImageSource
    env: dict[str, str] = field(default_factory=dict)
    project_name: str = "mirumoji"
