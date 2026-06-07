"""
Defines deterministic constants used by the launcher

info: Deterministic Data
    - Source Repository URL
    - Docker Image References
    - Docker Compose Identifiers
    - Environment Variables Used By The Server
"""

from .models import Backend, EnvVar

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

FRONTEND_IMAGE = "svdc1/mirumoji:frontend-latest"
"""
Docker Hub Identifier of the latest `Mirumoji` frontend image
"""
BACKEND_CPU_IMAGE = "svdc1/mirumoji:backend-cpu-latest"
"""
Docker Hub Identifier of the latest `Mirumoji` backend image for the `modal`
transcription backend
"""
BACKEND_GPU_IMAGE = "svdc1/mirumoji:backend-gpu-latest"
"""
Docker Hub Identifier of the latest `Mirumoji` backend image for the `local`
transcription backend
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
            "Set To 1 To Force Modal Containers To Update The Cached"
            "Mirumoji App Image"
        ),
        default="0",
    ),
)
"""
Modal Credentials + Configuration Environment Variables (Required Only For The
Modal Transcription Backend)
"""


PASSTHROUGH_VARS: tuple[str, ...] = (
    "MIRUMOJI_LOGGING_LEVEL",
    "MIRUMOJI_MODAL_IMAGE",
    "MIRUMOJI_SRT_DEFAULT_SYS_MSG",
    "MIRUMOJI_BREAKDOWN_DEFAULT_SYS_MSG",
)
"""
Additional environment variables accepted by the `mirumoji` backend that are
not required, but may be used for advanced configuration. All of these have
sensible defaults and don't require custom values in most cases
"""


# Set Automatically By The Launcher (Not User-Supplied)
HOST_LAN_IP_VAR = "HOST_LAN_IP"
"""
Stores the end-user's IPv4 LAN IP, discovered automatically with the `sockets`
library
"""

TRANSCRIBE_BACKEND_VAR = "MIRUMOJI_TRANSCRIBE_BACKEND"
"""
Stores a `Backend` value to be passed to the `mirumoji` server on
application startup
"""


# --- Internal ---

_GPU_PROBE_IMAGE = "nvidia/cuda:12.3.0-base-ubuntu22.04"
"""
The Docker Image used to verify that the system has a working version of the
`NVIDIA Container Toolkit`. The `local` transcribe-backend Image requires it
in order to have access to the GPU
"""


def prompted_vars(backend: Backend) -> tuple[EnvVar, ...]:
    """
    Returns the environment variables that the launcher should prompt for
    based on which mirumoji transcription backend is being used

    All LLM Provider API Keys are always offered, and are all optional.
    Modal credentials are added only when the Modal backend is selected

    Args:
        backend (Backend): The chosen transcription backend

    Returns:
        The ordered env vars to prompt for
    """
    if backend is Backend.MODAL:
        return (*LLM_VARS, *MODAL_VARS)
    return LLM_VARS
