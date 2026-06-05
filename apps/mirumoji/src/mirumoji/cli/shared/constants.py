"""
Defines deterministic constants uses by the launcher

info: Deterministic Data
    - Source Repository URL
    - Docker Image References
    - Docker Compose Identifiers
    - Environment Variables Used By The Server
"""

from .models import Backend, EnvVar

# --- Source Repository ---

REPO_URL = "https://github.com/svdC1/mirumoji.git"
DEFAULT_BRANCH = "main"

# --- Compose Identifiers ---

PROJECT_NAME = "mirumoji"
FRONTEND_SERVICE = "frontend"
BACKEND_SERVICE = "backend"

# --- Docker Image References ---

FRONTEND_IMAGE = "svdc1/mirumoji:frontend-latest"
BACKEND_CPU_IMAGE = "svdc1/mirumoji:backend-cpu-latest"
BACKEND_GPU_IMAGE = "svdc1/mirumoji:backend-gpu-latest"

# Tags Assigned To Images Built Locally
FRONTEND_LOCAL_IMAGE = "mirumoji_frontend_local:latest"
BACKEND_CPU_LOCAL_IMAGE = "mirumoji_backend_cpu_local:latest"
BACKEND_GPU_LOCAL_IMAGE = "mirumoji_backend_gpu_local:latest"

# --- Local Build Inputs (Relative To The Managed Repo Checkout Root) ---

FRONTEND_DOCKERFILE = "apps/frontend/Dockerfile"
FRONTEND_CONTEXT = "apps/frontend"
BACKEND_CONTEXT = "apps/mirumoji"
BACKEND_CPU_DOCKERFILE = (
    "apps/mirumoji/src/mirumoji/docker/Dockerfile.local.cpu"
)
BACKEND_GPU_DOCKERFILE = (
    "apps/mirumoji/src/mirumoji/docker/Dockerfile.local.gpu"
)

# --- Environment Variables ---

LLM_VARS: tuple[EnvVar, ...] = (
    EnvVar(
        "OPENAI_API_KEY",
        secret=True,
        description="OpenAI API Key (GPT)",
    ),
    EnvVar(
        "ANTHROPIC_API_KEY",
        secret=True,
        description="Anthropic API Key (Claude)",
    ),
    EnvVar(
        "GEMINI_API_KEY",
        secret=True,
        description="Google API Key (Gemini)",
    ),
    EnvVar(
        "MIRUMOJI_LLM_API_KEY",
        secret=True,
        description="API Key For A Custom OpenAI-Compatible Endpoint",
    ),
    EnvVar(
        "MIRUMOJI_LLM_BASE_URL",
        description="Base URL For A Custom OpenAI-Compatible Endpoint",
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
        description="Modal GPU Type",
        default="A10G",
    ),
    EnvVar(
        "MODAL_FORCE_BUILD",
        description=(
            "Whether To Force Modal To Pull The Latest `mirumoji-gpu`"
            "Ephemeral App Image When Starting Up A Container Instead Of Using"
            "An Account-Cached One"
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
Environment variables that are always passed through to the backend container
when present, but never prompted for since sensible server defaults exist
"""


# Set Automatically By The Launcher (Not User-Supplied)
HOST_LAN_IP_VAR = "HOST_LAN_IP"
TRANSCRIBE_BACKEND_VAR = "MIRUMOJI_TRANSCRIBE_BACKEND"

# --- Internal ---

_GPU_PROBE_IMAGE = "nvidia/cuda:12.3.0-base-ubuntu22.04"
"""
The Docker Image used to verify that the system has a working version of the
`NVIDIA Container Toolkit`. The `local` transcribe-backend Image requires it
in order to have access to the GPU
"""


def prompted_vars(backend: Backend) -> tuple[EnvVar, ...]:
    """
    Returns the env vars the launcher should prompt for, per backend

    LLM keys are always offered (optional); Modal credentials are added only
    when the Modal backend is selected

    Args:
        backend (Backend): The chosen transcription backend

    Returns:
        The ordered env vars to prompt for
    """
    if backend is Backend.MODAL:
        return (*LLM_VARS, *MODAL_VARS)
    return LLM_VARS
