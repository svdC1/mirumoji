"""
This module defines the `health_router` of the Mirumoji API.

Attributes:
  health_router (APIRouter): The FastAPI Router Object
"""

import asyncio

from fastapi import APIRouter

from ..config import get_system_info
from ..models.responses import HealthStatusResponse, SystemInfoResponse

health_router = APIRouter(prefix="/health")


@health_router.get("/status", response_model=HealthStatusResponse)
async def health_check() -> HealthStatusResponse:
    """
    Minimal ping endpoint to check if the API is running

    Returns:
        UP status confirmation
    """
    return HealthStatusResponse(status="ok")


@health_router.get("/system", response_model=SystemInfoResponse)
async def gpu_check() -> SystemInfoResponse:
    """
    Collects information about the system running the API, including OS, GPUs,
    Python Version , etc

    info: Off The Event Loop
        `get_system_info` shells out to `nvidia-smi`, so it runs in a thread to
        avoid blocking the event loop while it waits

    Returns:
        Information about the system running the API
    """
    info = await asyncio.to_thread(get_system_info)
    return SystemInfoResponse(**info)
