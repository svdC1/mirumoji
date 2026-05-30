"""
This module defines the `llm_router` of the Mirumoji API

Attributes:
    LOGGER (logging.Logger): Module's Logging object
    llm_router (APIRouter): The FastAPI Router object
"""

import logging

from fastapi import APIRouter

from ..processing.llm import provider_status

LOGGER = logging.getLogger(__name__)
llm_router = APIRouter(prefix="/llm")


@llm_router.get("/providers")
async def list_providers() -> dict:
    """
    Report which LLM providers are usable in this deployment

    Returns:
        Mapping with a `providers` list of `{"provider", "available"}` entries,
            used by the frontend to populate the model picker
    """
    return {"providers": provider_status()}
