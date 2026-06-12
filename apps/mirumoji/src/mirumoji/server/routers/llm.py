"""
This module defines the `llm_router` of the Mirumoji API

Attributes:
    LOGGER (logging.Logger): Module's logging object
    llm_router (APIRouter): The FastAPI router object
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...exceptions import LLMRequestError
from ..config import get_settings
from ..models.requests import (
    BreakdownRequest,
    ChatRequest,
    ExplainSentenceRequest,
    FixSrtRequest,
)
from ..models.responses import (
    BreakdownResponse,
    ExplanationResponse,
    FixSrtResponse,
)
from ..processing import llm, text
from ..processing.subtitles import sanitize_srt

LOGGER = logging.getLogger(__name__)
llm_router = APIRouter(prefix="/llm")


@llm_router.get("/providers")
async def list_providers() -> dict[str, Any]:
    """
    Reports which LLM providers are usable in this deployment

    Returns:
        Mapping with a `providers` list of `{"provider", "available"}` entries,
            used by the frontend to populate the model picker
    """
    return {"providers": llm.provider_status()}


@llm_router.post("/breakdown", response_model=BreakdownResponse)
async def breakdown(req: BreakdownRequest) -> BreakdownResponse:
    """
    Explains the nuance of a focus word within a sentence

    `sys_msg` and `prompt` are independently optional and fall back to the
    default breakdown system message and prompt

    Args:
        req (BreakdownRequest): The breakdown request

    Returns:
        The focused `EnrichedJapaneseWord` (when a focus is given) and the LLM
            explanation

    Raises:
        InvalidModelStringError: If the model selector is malformed
        LLMProviderUnavailableError: If the requested provider isn't configured
        LLMRequestError: If the prompt template is invalid or the request fails
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

    explanation = await asyncio.to_thread(
        client.complete,
        system=system,
        prompt=prompt,
        model=model,
    )

    focus_word = None
    if req.focus:
        words = await asyncio.to_thread(text.enrich, req.focus)
        focus_word = words[0] if words else None

    return BreakdownResponse(focus=focus_word, explanation=explanation)


@llm_router.post("/explain_sentence", response_model=ExplanationResponse)
async def explain_sentence(
    req: ExplainSentenceRequest,
) -> ExplanationResponse:
    """
    Explains a whole sentence, without a focus word

    `sys_msg` and `prompt` are independently optional and fall back to the
    default breakdown system message and sentence prompt

    Args:
        req (ExplainSentenceRequest): The explanation request

    Returns:
        The LLM explanation

    Raises:
        InvalidModelStringError: If the model selector is malformed
        LLMProviderUnavailableError: If the requested provider isn't configured
        LLMRequestError: If the prompt template is invalid or the request fails
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

    explanation = await asyncio.to_thread(
        client.complete,
        system=system,
        prompt=prompt,
        model=model,
    )
    return ExplanationResponse(explanation=explanation)


@llm_router.post("/fix_srt", response_model=FixSrtResponse)
async def fix_srt(req: FixSrtRequest) -> FixSrtResponse:
    """
    Cleans up raw SRT content with an LLM

    Args:
        req (FixSrtRequest): The SRT-fix request

    Returns:
        The cleaned-up SRT content

    Raises:
        InvalidModelStringError: If the model selector is malformed
        LLMProviderUnavailableError: If the requested provider isn't configured
        LLMRequestError: If the request fails
    """
    client, model = llm.client_for_model(req.model)
    system = req.sys_msg or get_settings().srt_sys_msg
    fixed = await asyncio.to_thread(
        client.complete,
        system=system,
        prompt=req.srt,
        model=model,
    )
    # Repair any timestamps the LLM may have corrupted before returning/saving.
    return FixSrtResponse(srt=sanitize_srt(fixed))


@llm_router.post("/stream")
async def stream(req: ChatRequest) -> StreamingResponse:
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
