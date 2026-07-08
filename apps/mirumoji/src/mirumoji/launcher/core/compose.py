"""
Defines helpers to modify the Docker Compose template at
`mirumoji/docker/compose/compose.yaml` according to user input

info: Additional Information
    - A single annotated template ships in the package
      (`mirumoji/docker/compose/compose.yaml`)

    - This module loads it, rewrites the image references and GPU wiring for
      the chosen backend + image source, and writes the resolved file that
      the lifecycle commands run with
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from ...paths import COMPOSE_TEMPLATE_PATH, HOST_RENDER_DIR
from .constants import (
    BACKEND_CPU_IMAGE,
    BACKEND_CPU_LOCAL_IMAGE,
    BACKEND_GPU_IMAGE,
    BACKEND_GPU_LOCAL_IMAGE,
    BACKEND_SERVICE,
    FRONTEND_IMAGE,
    FRONTEND_LOCAL_IMAGE,
    FRONTEND_SERVICE,
)
from .models import Backend, ImageSource

LOGGER = logging.getLogger(__name__)

RESOLVED_COMPOSE_PATH: Path = HOST_RENDER_DIR / "compose.resolved.yaml"
"""
Defines the path in which to save the edited Docker Compose file
"""

_GPU_DEPLOY: dict[str, Any] = {
    "resources": {
        "reservations": {
            "devices": [
                {
                    "driver": "nvidia",
                    "count": 1,
                    "capabilities": ["gpu"],
                },
            ],
        },
    },
}
"""
Defines The NVIDIA GPU reservation injected into the backend service when using
the `local` transcription backend
"""


_HF_CACHE_MOUNT = "huggingface_cache:/root/.cache/huggingface"
"""
Defines The HuggingFace Model Cache Volume Mounted In The Local Transcription
Backend To Store The Faster Whisper Model Weights
"""

_HF_CACHE_VOLUME = "huggingface_cache"
"""
Defines The Name Of The HuggingFace Model Cache Volume Mounted In The Local
Transcription Backend To Store The Faster Whisper Model Weights
"""


def _backend_image(backend: Backend, source: ImageSource) -> str:
    """
    Determines which backend image reference to use based on a `backend` +
    `source` pair

    Args:
        backend (Backend): The chosen transcription backend
        source (ImageSource): Pull vs local build

    Returns:
        The image reference to set on the backend service
    """
    if source is ImageSource.BUILD:
        if backend is Backend.LOCAL:
            return BACKEND_GPU_LOCAL_IMAGE
        return BACKEND_CPU_LOCAL_IMAGE
    if backend is Backend.LOCAL:
        return BACKEND_GPU_IMAGE
    return BACKEND_CPU_IMAGE


def _frontend_image(source: ImageSource) -> str:
    """
    Determines which frontend image reference to use for a given image `source`

    Args:
        source (ImageSource): Pull vs local build

    Returns:
        The image reference to set on the frontend service
    """
    if source is ImageSource.BUILD:
        return FRONTEND_LOCAL_IMAGE
    return FRONTEND_IMAGE


def load_template() -> dict[str, Any]:
    """
    Loads the packaged compose template using `PyYAML`

    Returns:
        The parsed template as a mutable dict

    Raises:
        FileNotFoundError: If the packaged template is missing
    """
    with COMPOSE_TEMPLATE_PATH.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data


def transform(
    template: dict[str, Any],
    backend: Backend,
    source: ImageSource,
) -> dict[str, Any]:
    """
    Edits the `template` returned by `load_template` in place according to the
    chosen transcription `backend` and image `source`

    info: Edits Performed
        - Sets both services' image references according to `backend` and
          `source`

        - Adds the NVIDIA GPU reservation + Hugging Face model-cache volume if
          `backend=local`

    Args:
        template (dict[str, Any]): The parsed packaged compose template
        backend (Backend): The chosen transcription backend
        source (ImageSource): Pull vs local build

    Returns:
        The same template dict, now resolved
    """
    services: dict[str, Any] = template["services"]
    # Set Frontend Image Reference
    services[FRONTEND_SERVICE]["image"] = _frontend_image(source)

    backend_svc: dict[str, Any] = services[BACKEND_SERVICE]
    # Set Backend Image Reference
    backend_svc["image"] = _backend_image(backend, source)

    if backend is Backend.LOCAL:
        # Attatch GPU Capability
        backend_svc["deploy"] = _GPU_DEPLOY
        # Get Inner `volumes` Key In Backend Service Or Create It If It
        # Doesn't Exist
        backend_volumes: list[str] = backend_svc.setdefault("volumes", [])
        # Attatch Hugging Face Cache Volume If It Doesn't Exist
        if _HF_CACHE_MOUNT not in backend_volumes:
            backend_volumes.append(_HF_CACHE_MOUNT)

        # Get The Outer `volumes` Key From The Docker Compose File Or Create
        # It If It Doesn't Exist.
        template_volumes = template.setdefault("volumes", {})
        # Set The Empty `hugging_face` Volume Key
        template_volumes[_HF_CACHE_VOLUME] = None
    else:
        # Remove GPU Capability If It Already Existed
        backend_svc.pop("deploy", None)

    return template


def write_compose(
    backend: Backend,
    source: ImageSource,
    *,
    out_path: Path = RESOLVED_COMPOSE_PATH,
) -> Path:
    """
    Writes a resolved compose file for the chosen `backend` + `source`

    Args:
        backend (Backend): The chosen mirumoji transcription backend
        source (ImageSource): Pull vs local build
        out_path (Path): Where to write the resolved file

    Returns:
        The path to the written compose file

    Raises:
        FileNotFoundError: If the packaged template is missing
    """
    resolved = transform(load_template(), backend, source)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            data=resolved,
            stream=fh,
            indent=4,
            sort_keys=False,
            default_flow_style=False,
        )
    LOGGER.debug(f"Wrote Compose File To {out_path}")
    return out_path
