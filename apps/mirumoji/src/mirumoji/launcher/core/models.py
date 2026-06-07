"""
Defines data structures containing information used to determine how to
correctly start the mirumoji Docker Compose application

info: Additional Information
    This information is used by the launcher (CLI + GUI) to determine the
    following

    - Which mirumoji transcription backend to use (`Backend`)

    - Whether to pull the application's pre-built Docker Images from Docker
      Hub, or whether to clone the mirumoji repo and build the application's
      images locally (`ImageSource`)

    - All of the environment variables expected by mirumoji, whether or not
      they are optional, their default value, and what they represent (`EnvVar`
      )

    - The `status` of every external dependency used by mirumoji in the
      end-user's machine. Whether or not it's available in the end-user's
      machine, or whether the launcher couldn't check for it (`CheckStatus`,
      `CheckResult`)

    - All information to pass to Docker Compose in order to correctly start
      the mirumoji application based on the end-user's choices (`ComposeSpec`)

"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Backend(str, Enum):
    """
    Defines all possible mirumoji transcription backend options

    info: Backends
        `Mirumoji` uses `faster-whisper` to handle video transcriptions and
        `FFMPEG` to handle media operations. For long media, these tools can
        become very time-consuming unless they're run on a GPU. Therefore,
        mirumoji offers the option to run them either on a `LOCAL` NVIDIA GPU,
        or on a `MODAL` GPU container. When running them on a `MODAL`
        container, the end-user's machine doesn't need to have an NVDIA GPU to
        run mirumoji

    Attributes:
        LOCAL: Use the GPU image with `faster-whisper` running on the host
        MODAL: Use the CPU image and off-load transcription to Modal GPU
            containers
    """

    LOCAL = "local"
    MODAL = "modal"

    def __str__(self) -> str:
        """
        Renders the option as a plain string (e.g. `modal`) for prompts and
        help text

        Returns:
            The backend's string value
        """
        return self.value


class ImageSource(str, Enum):
    """
    Defines all possible sources from where to acquire the mirumoji Docker
    Compose application's Docker Images

    info: Image Sources
        - The `Mirumoji` Docker Compose application runs 2 Docker Images

        - The `frontend` image uses `Nginx` along with a self-signed SSL
          certificate to run the React application and make it available
          across the end-user's network

        - The `backend` image runs the Python FastAPI application, which
          exposes the API that the React application relies on for media
          processsing, tokenization, dictionary access, etc

        - Both images are pre-built by mirumoji's GitHub CI action and
          published to Docker Hub, so that end-user's don't have to build them
          themselves. The `PULL` option tells Docker Compose to pull these
          pre-built images instead of building them locally

        - If for any reason an end-user wants to build the images themselves,
          the `BUILD` option tells the launcher to clone the `mirumoji` repo
          from GitHub, build the images in the end-user's machine, and point
          the Docker Compose application to the locally built images instead
          of trying to pull the pre-built ones

    Attributes:
        PULL: Pull the pre-built images from Docker Hub
        BUILD: Build the frontent + backend images locally from a local
            mirumoji repo clone
    """

    PULL = "pull"
    BUILD = "build"


@dataclass(frozen=True)
class EnvVar:
    """
    Represents a single environment variable used by the mirumoji application

    info: Environment Variables
        `Mirumoji` offers various configuration options and they're all
        resolved from environment variables. In addition, some environment
        variables are also used internally to correclty setup the application,
        for example, the `HOST_LAN_IP` variable, which is used to correctly
        generate the self-signed SSL certificate used by the `frontend` image
        to serve the React application via HTTPS. For more information on
        all environment variables, view `core.constants`

    Attributes:
        name (str): Name of the environment variable
        required (bool): Whether the chosen transcription backend needs it to
            be set
        secret (bool): Whether prompts should hide the typed value (API Keys)
        description (str): Human-facing description of what the variable
            represents in the context of the application
        default (str): The default value applied when the user doesn't provide
            it (Non-Required Only)
    """

    name: str
    required: bool = False
    secret: bool = False
    description: str = ""
    default: str = ""


class CheckStatus(str, Enum):
    """
    Represents the status of an external dependecy used by mirumoji in the
    end-user's machine

    Attributes:
        OK: The dependency is present and working
        MISSING: The dependency is absent or not functioning
        SKIPPED: The dependency is not needed for the chosen
            backend and wasn't checked
    """

    OK = "ok"
    MISSING = "missing"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class CheckResult:
    """
    Represents the result of a validation check performed by the launcher to
    inspect a specific external dependency

    Attributes:
        name (str): The dependency that was checked (e.g. `"Docker"`)
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
    Represents all information to pass to Docker Compose in order to correctly
    start the mirumoji application based on the end-user's choices

    Attributes:
        backend (Backend): Which mirumoji transcription backend to use
        source (ImageSource): Whether to pull pre-built images from Docker Hub
            , or build them locally
        env (dict[str, str]): All environment variables to pass to the Docker
            Compose Application
        project_name (str): The compose project name
    """

    backend: Backend
    source: ImageSource
    env: dict[str, str] = field(default_factory=dict)
    project_name: str = "mirumoji"
