"""
This module defines the `health_router` of the Mirumoji API.

Attributes:
  health_router (APIRouter): The FastAPI Router Object.
"""


from fastapi import APIRouter
from utils.system_info_utils import get_system_info

health_router = APIRouter(prefix="/health")


@health_router.get("/status")
async def health_check():
    """
    Endpoint for checking if API is running.

    Returns:
      dict: Up status confirmation.
    """
    return {"status": "ok"}


@health_router.get("/system")
async def gpu_check():
    """
    Endpoint for checking information about the system
    running the API

    Returns:
      dict: Information about the system running the API.
    """
    return get_system_info()
