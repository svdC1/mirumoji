"""
This module defines the `llm_router` of the Mirumoji API

Attributes:
    LOGGER (logging.Logger): Module's logging object
    llm_router (APIRouter): The FastAPI router object
"""

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Body, Query
from fastapi.responses import StreamingResponse

from ...exceptions import InvalidModelStringError, LLMRequestError
from ..config import get_settings
from ..models.requests import (
    BreakdownRequest,
    ChatRequest,
    ExplainSentenceRequest,
)
from ..models.responses import (
    ModelsResponse,
    ProvidersResponse,
    ProviderStatusResponse,
)
from ..processing import llm, text

LOGGER = logging.getLogger(__name__)
llm_router = APIRouter(prefix="/llm")


@llm_router.get("/providers", response_model=ProvidersResponse)
async def list_providers() -> ProvidersResponse:
    """
    Reports which LLM providers are usable in this deployment

    Returns:
        A `providers` list of `{"provider", "available"}` entries, used by the
            frontend to populate the model picker
    """
    return ProvidersResponse(
        providers=[ProviderStatusResponse(**p) for p in llm.provider_status()]
    )


@llm_router.get("/models", response_model=ModelsResponse)
async def list_models(
    provider: Annotated[str, Query()],
) -> ModelsResponse:
    """
    Lists the available models for a configured LLM provider

    Lets the frontend offer a model dropdown for the cloud providers, so users
    pick a valid model instead of typing one that 404s

    Args:
        provider (str): The provider id (`openai`, `anthropic`, `gemini`,
            `local`)

    Returns:
        Mapping with a `models` list of model ids

    Raises:
        InvalidModelStringError: If the provider id is unknown
        LLMProviderUnavailableError: If the provider isn't configured
        LLMRequestError: If the provider's models endpoint fails
    """
    try:
        prov = llm.LLMProvider(provider)
    except ValueError as e:
        raise InvalidModelStringError(
            f"Unknown LLM provider '{provider}'",
            details={"provider": provider},
        ) from e
    models = await asyncio.to_thread(llm.available_models, prov)
    return ModelsResponse(models=models)


@llm_router.post("/breakdown")
async def breakdown(
    req: Annotated[BreakdownRequest, Body()],
) -> StreamingResponse:
    """
    Streams the nuance of a focus word within a sentence as Server-Sent Events

    The focus word (its stitched token + dictionary data) is emitted once as a
    `focus` event, then the LLM explanation streams as `data:` frames

    `sys_msg` and `prompt` are independently optional and fall back to the
    default breakdown system message and prompt

    Args:
        req (BreakdownRequest): The breakdown request

    Returns:
        An SSE stream: a `focus` frame (when a focus is given), the explanation
            chunks, and a terminal `done` frame

    Raises:
        InvalidModelStringError: If the model selector is malformed
        LLMProviderUnavailableError: If the requested provider isn't configured
        LLMRequestError: If the prompt template is invalid
    """
    client, model = llm.client_for_model(req.model)
    focus = req.focus or ""

    if req.prompt is not None:
        system, prompt = llm.custom_breakdown_prompt(
            req.sentence,
            focus,
            req.sys_msg or get_settings().breakdown_sys_msg,
            req.prompt,
        )
    else:
        default_system, prompt = llm.default_breakdown_prompt(
            req.sentence,
            focus,
        )
        system = req.sys_msg or default_system

    focus_json: str | None = None
    if req.focus:
        words = await asyncio.to_thread(text.enrich, req.focus)
        if words:
            focus_json = words[0].model_dump_json()

    chunks = client.stream(system=system, prompt=prompt, model=model)
    return StreamingResponse(
        llm.sse_breakdown(focus_json, chunks),
        media_type="text/event-stream",
    )


@llm_router.post("/explain_sentence")
async def explain_sentence(
    req: Annotated[ExplainSentenceRequest, Body()],
) -> StreamingResponse:
    """
    Streams an explanation of a whole sentence as Server-Sent Events

    `sys_msg` and `prompt` are independently optional and fall back to the
    default breakdown system message and sentence prompt

    Args:
        req (ExplainSentenceRequest): The explanation request

    Returns:
        An SSE stream of explanation chunks ending with a `done` frame

    Raises:
        InvalidModelStringError: If the model selector is malformed
        LLMProviderUnavailableError: If the requested provider isn't configured
        LLMRequestError: If the prompt template is invalid
    """
    client, model = llm.client_for_model(req.model)

    if req.prompt is not None:
        try:
            prompt = req.prompt.format(req.sentence)
        except (IndexError, KeyError, ValueError) as e:
            raise LLMRequestError(
                f"Invalid custom prompt template: {e}",
            ) from e
        system = req.sys_msg or get_settings().breakdown_sys_msg
    else:
        default_system, prompt = llm.sentence_breakdown_prompt(req.sentence)
        system = req.sys_msg or default_system

    chunks = client.stream(system=system, prompt=prompt, model=model)
    return StreamingResponse(
        llm.sse_format(chunks),
        media_type="text/event-stream",
    )


@llm_router.post("/stream")
async def stream(req: Annotated[ChatRequest, Body()]) -> StreamingResponse:
    """
    Streams a chat completion as Server-Sent Events

    Args:
        req (ChatRequest): The chat request

    Returns:
        An SSE stream of completion chunks ending with a `done` event

    Raises:
        InvalidModelStringError: If the model selector is malformed
        LLMProviderUnavailableError: If the requested provider isn't configured
    """
    client, model = llm.client_for_model(req.model)
    system = req.system_message or "You are a helpful assistant."
    chunks = client.stream(system=system, prompt=req.prompt, model=model)
    return StreamingResponse(
        llm.sse_format(chunks),
        media_type="text/event-stream",
    )
