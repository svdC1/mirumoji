"""
This module defines the `health_router` of the Mirumoji API.

Attributes:
  health_router (APIRouter): The FastAPI Router Object
"""

from typing import Any

from fastapi import APIRouter

from ..config import get_system_info

health_router = APIRouter(prefix="/health")


@health_router.get("/status")
async def health_check() -> dict[str, str]:
    """
    Minimal ping endpoint to check if the API is running

    Returns:
        UP status confirmation
    """
    return {"status": "ok"}


@health_router.get("/system")
async def gpu_check() -> dict[str, Any]:
    """
    Collects information about the system running the API, including OS, GPUs,
    Python Version , etc

    Returns:
        Information about the system running the API
    """
    return get_system_info()
