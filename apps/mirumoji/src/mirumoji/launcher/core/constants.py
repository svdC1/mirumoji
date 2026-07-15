"""
Defines deterministic constants used by the launcher

info: Deterministic Data
    - Source Repository URL
    - Docker Image References
    - Docker Compose Identifiers
    - Environment Variables Used By The Server
    - Environment Variables Used By The Modal Host Option
"""

from .models import Backend, EnvVar, ImageSource

# --- Source Repository ---

REPO_URL = "https://github.com/svdC1/mirumoji.git"
"""
The `Mirumoji` GitHub repository URL
"""

DEFAULT_BRANCH = "main"
"""
Which branch of the `Mirumoji` GitHub repo to use to build images
"""


# --- Compose Identifiers ---

PROJECT_NAME = "mirumoji"
"""
Name of the Docker Compose project
"""

FRONTEND_SERVICE = "frontend"
"""
Identifier for the frotend service in the `Mirumoji` Docker Compose application
"""

BACKEND_SERVICE = "backend"
"""
Identifier for the backend service in the `Mirumoji` Docker Compose application
"""

# --- Docker Image References ---

FRONTEND_IMAGE = "svdc1/mirumoji:frontend-{version}"
"""
String template for a Docker Hub Identifier of the `Mirumoji`
frontend image
"""
BACKEND_CPU_IMAGE = "svdc1/mirumoji:backend-cpu-{version}"
"""
String template for a Docker Hub Identifier of the `Mirumoji` backend image for
the `modal` transcription backend
"""
BACKEND_GPU_IMAGE = "svdc1/mirumoji:backend-gpu-{version}"
"""
String template for Docker Hub Identifier of the `Mirumoji` backend image
for the `local` transcription backend
"""

# Tags Assigned To Images Built Locally
FRONTEND_LOCAL_IMAGE = "mirumoji_frontend_local:latest"
"""
Local Docker Image Identifier to attach to a locally built `Mirumoji` frontend
image
"""
BACKEND_CPU_LOCAL_IMAGE = "mirumoji_backend_cpu_local:latest"
"""
Local Docker Image Identifier to attach to a locally built `Mirumoji` backend
image for the `modal` transcription backend
"""
BACKEND_GPU_LOCAL_IMAGE = "mirumoji_backend_gpu_local:latest"
"""
Local Docker Image Identifier to attach to a locally built `Mirumoji` backend
image for the `local` transcription backend
"""

# --- Local Build Inputs (Relative To The Managed Repo Checkout Root) ---

FRONTEND_DOCKERFILE = "apps/frontend/Dockerfile"
"""
Path to the `fontend` Docker Image's `Dockerfile` relative to the `mirumoji`
repo root
"""
FRONTEND_CONTEXT = "apps/frontend"
"""
Path determining the location relative to the `mirumoji` repo's root from
which Docker should build the `frontend` Image
"""
BACKEND_CONTEXT = "apps/mirumoji"
"""
Path determining the location relative to the `mirumoji` repo's root from
which Docker should build the `backend` Image
"""
BACKEND_CPU_DOCKERFILE = (
    "apps/mirumoji/src/mirumoji/docker/Dockerfile.local.cpu"
)
"""
Path to the `backend` Docker Image's `Dockerfile` relative to the `mirumoji`
repo root when using the `modal` transcription backend
"""
BACKEND_GPU_DOCKERFILE = (
    "apps/mirumoji/src/mirumoji/docker/Dockerfile.local.gpu"
)
"""
Path to the `backend` Docker Image's `Dockerfile` relative to the `mirumoji`
repo root when using the `local` transcription backend
"""

# --- Environment Variables ---

LLM_VARS: tuple[EnvVar, ...] = (
    EnvVar(
        "OPENAI_API_KEY",
        secret=True,
        description="Make GPT Available For LLM Features",
    ),
    EnvVar(
        "ANTHROPIC_API_KEY",
        secret=True,
        description="Make Claude Available For LLM Features",
    ),
    EnvVar(
        "GEMINI_API_KEY",
        secret=True,
        description="Make Gemini Available For LLM Features",
    ),
    EnvVar(
        "MIRUMOJI_LLM_API_KEY",
        secret=True,
        description=(
            "Use A Custom OpenAI-Compatible Endpoint For LLM Features"
            " (Leave Empty If Not Applicable)"
        ),
    ),
    EnvVar(
        "MIRUMOJI_LLM_BASE_URL",
        description="Use A Custom OpenAI-Compatible Endpoint For LLM Features",
    ),
)
"""
Optional LLM Provider Keys

The frontend gates the use of LLM capabilities when none of these are
configured
"""

MODAL_VARS: tuple[EnvVar, ...] = (
    EnvVar(
        "MODAL_TOKEN_ID",
        required=True,
        secret=True,
        description="Modal Token ID (Required For The Modal Backend)",
    ),
    EnvVar(
        "MODAL_TOKEN_SECRET",
        required=True,
        secret=True,
        description="Modal Token Secret (Required For The Modal Backend)",
    ),
    EnvVar(
        "MIRUMOJI_MODAL_GPU",
        description="Which GPU To Use In The Modal Containers",
        default="A10G",
    ),
    EnvVar(
        "MODAL_FORCE_BUILD",
        description=(
            "Forces Modal Containers To Update The Cached Mirumoji App Image"
        ),
        default="0",
    ),
)
"""
Modal Credentials + Configuration Environment Variables (Required Only For The
Modal Transcription Backend)
"""


ADVANCED_VARS: tuple[EnvVar, ...] = (
    EnvVar(
        "MIRUMOJI_LOGGING_LEVEL",
        description="The Python Logging Level For The Mirumoji Backend Server",
    ),
    EnvVar(
        "MIRUMOJI_MODAL_IMAGE",
        description="Docker Hub Image That Modal Containers Will Run",
    ),
    EnvVar(
        "MIRUMOJI_MODAL_SCALEDOWN_WINDOW",
        description=(
            "Seconds To Keep An Idle Modal GPU Container Warm Before It "
            "Scales Down (Higher Speeds Up Back-To-Back Jobs At A Higher Cost)"
        ),
        default="60",
    ),
    EnvVar(
        "MIRUMOJI_MAX_LLM_CONCURRENCY",
        description=(
            "How Many LLM Requests Run At Once When Fixing A Batch Of "
            "Subtitles"
        ),
        default="4",
    ),
    EnvVar(
        "MIRUMOJI_SRT_DEFAULT_SYS_MSG",
        description=(
            "The Default LLM System Message Used For SRT Fixing When A "
            "Profile Doesn't Have An LLM Template Configured"
        ),
    ),
    EnvVar(
        "MIRUMOJI_BREAKDOWN_DEFAULT_SYS_MSG",
        description=(
            "The Default LLM System Message Used For Word Breakdowns When A "
            "Profile Doesn't Have An LLM Template Configured"
        ),
    ),
)
"""
Additional environment variables accepted by the `mirumoji` backend that are
not required, but may be used for advanced configuration. All of these have
sensible defaults and don't require custom values in most cases
"""


MODAL_HOST_VARS: tuple[EnvVar, ...] = (
    EnvVar(
        "MIRUMOJI_WEB_PASSWORD",
        secret=True,
        description=(
            "Login Password For The Modal-Hosted App (Generated On First "
            "Deploy When Unset)"
        ),
    ),
    EnvVar(
        "MIRUMOJI_HOST_MAX_CONCURRENT_REQUESTS",
        default="100",
        description=(
            "How Many Requests The Modal-Hosted App Container Serves At Once"
        ),
    ),
    EnvVar(
        "MIRUMOJI_HOST_CPU",
        default="2",
        description=(
            "CPU Cores Reserved For The Always-Warm Modal-Hosted Web "
            "Container (Higher Is Faster But Costs More)"
        ),
    ),
    EnvVar(
        "MIRUMOJI_HOST_MEMORY",
        default="4096",
        description=(
            "Memory In MiB Reserved For The Always-Warm Modal-Hosted Web "
            "Container (Higher Avoids Restarts But Costs More)"
        ),
    ),
)
"""
Environment variables specific to the Modal-hosted deploy

The login username is always `mirumoji`, only the password is configurable

info: GPU Tasks In Modal-Hosted App
    - The app deployed by `mirumoji modal deploy` uses the same
      offload worker (a second, GPU-enabled modal app) that the
      server's `modal` transcription backend uses

    - This means that all of the Modal-related environment variables
      in `MODAL_VARS` and `ADVANCED_VARS` also apply to the modal-hosted
      deploy app
"""


# Set Automatically By The Launcher (Not User-Supplied)
HOST_LAN_IP_VAR = "HOST_LAN_IP"
"""
Stores the end-user's IPv4 LAN IP, discovered automatically with the `socket`
library
"""

TRANSCRIBE_BACKEND_VAR = "MIRUMOJI_TRANSCRIBE_BACKEND"
"""
Stores a `Backend` value to be passed to the `mirumoji` server on
application startup
"""

IMAGE_SOURCE_VAR = "MIRUMOJI_IMAGE_SOURCE"
"""
Persists the launcher's image-source choice (pull pre-built vs build locally)
in the managed config file so that it's remembered across runs

Launcher-Only. The compose template never references it, and the server
ignores it
"""

VERSION_VAR = "MIRUMOJI_VERSION"
"""
Pins the published image version the launcher pulls (and composes the Modal
host from), defaulting to the installed package version

Launcher-Only. It fills the `{version}` in the image references above and is
never passed to the server or a container
"""


# --- Managed Config Surface ---

CONFIG_ENV_VARS: tuple[EnvVar, ...] = (
    *LLM_VARS,
    *MODAL_VARS,
    *ADVANCED_VARS,
    *MODAL_HOST_VARS,
)
"""
Every user-facing environment variable that the launcher manages in the config
file (LLM Providers + Modal + Advanced Overrides + Hosted Deploy)
"""

# Deployment keys are also env vars and are managed by the launcher,
# but they're validated against their respective enums rather than treated as
# free-form strings
_DEPLOYMENT_CHOICES: dict[str, tuple[str, ...]] = {
    TRANSCRIBE_BACKEND_VAR: tuple(b.value for b in Backend),
    IMAGE_SOURCE_VAR: tuple(s.value for s in ImageSource),
}

CONFIG_KEYS: frozenset[str] = frozenset(
    [v.name for v in CONFIG_ENV_VARS]
    + list(_DEPLOYMENT_CHOICES)
    + [VERSION_VAR]
)
"""
Every environment variable key that the launcher accepts in the managed config
file. Used to reject unknown keys in `mirumoji config set/delete`
"""


def is_config_key(key: str) -> bool:
    """
    Reports whether `key` is a recognised managed-config key

    Args:
        key (str): The candidate environment-variable name

    Returns:
        `True` when the key is managed by the launcher
    """
    return key in CONFIG_KEYS


def deployment_choices(key: str) -> tuple[str, ...] | None:
    """
    Returns the allowed values for a deployment key, or `None` for free-form
    keys

    Args:
        key (str): The environment variable key

    Returns:
        The permitted enum values for `MIRUMOJI_TRANSCRIBE_BACKEND` /
        `MIRUMOJI_IMAGE_SOURCE`, else `None`
    """
    return _DEPLOYMENT_CHOICES.get(key)


# --- Internal ---

_GPU_PROBE_IMAGE = "nvidia/cuda:12.3.0-base-ubuntu22.04"
"""
The Docker Image used to verify that the system has a working version of the
`NVIDIA Container Toolkit`. The `local` transcribe-backend Image requires it
in order to have access to the GPU
"""


def backend_vars(backend: Backend) -> tuple[EnvVar, ...]:
    """
    Returns all relevant environment variables for a given transcription
    `backend`

    info: `MODAL` Backend
        - All Modal-Related Variables
        - All LLM Provider API Keys
        - All Advanced Variables

    info: `LOCAL` Backend
        - All LLM Provider API Keys
        - All Advanced Variables

    Args:
        backend (Backend): The chosen transcription backend

    Returns:
        The ordered env vars that may be passed when the transcription backend
        choice is `backend`
    """
    if backend is Backend.MODAL:
        return (*LLM_VARS, *MODAL_VARS, *ADVANCED_VARS)
    return (*LLM_VARS, *ADVANCED_VARS)
