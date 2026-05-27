"""
This module defines the `gpt_router` of the Mirumoji API.

Attributes:
  LOGGER (logging.Logger): Module's Logging object.
  gpt_router (APIRouter): The FastAPI Router Object.
"""
import logging
import re
from fastapi import (APIRouter,
                     Query,
                     HTTPException,
                     Depends,
                     status)
from fastapi.responses import StreamingResponse
from typing import Optional, Dict

from mirumoji.server.processing.Processor import Processor
from mirumoji.server.models.ChatRequest import ChatRequest
from mirumoji.server.models.BreakdownRequest import BreakdownRequest
from mirumoji.server.models.BreakdownResponse import BreakdownResponse
from mirumoji.server.models.CustomBreakdownRequest import CustomBreakdownRequest
from mirumoji.server.utils.stream_utils import sse_gen
from mirumoji.server.profile_manager import get_profile_id_optional

LOGGER = logging.getLogger(__name__)

processor = Processor()
breakdown_service = processor.sentence_breakdown_service

gpt_router = APIRouter(prefix='/gpt')


@gpt_router.post("/breakdown", response_model=BreakdownResponse)
async def breakdown(
    req: BreakdownRequest,
    profile_id: Optional[str] = Depends(get_profile_id_optional)
) -> BreakdownResponse:
    """
    POST endpoint for analysing a Japanese sentence.

    Args:
      req (BreakdownRequest): JSON request matching `BreakdownRequest` model.
      profile_id (str, optional): Profile ID Header.

    Returns:
      dict: Dictionary containing fields of `BreakdownResonse` model.

    Raises:
      HTTPException: Status code 500 if breakdown fails.
    """
    LOGGER.info((f"Breakdown Request: sentence='{req.sentence!r}';"
                 f"focus='{req.focus!r}'")
                )
    try:
        result = breakdown_service.explain(req.sentence, req.focus)
        return result
    except Exception as e:
        LOGGER.warning(f"Breakdown Failed: '{e}'")
        cleaned = re.sub(r"[（）]", "", req.sentence)
        LOGGER.info(f"Retrying with clean sentence: '{cleaned!r}'")
        try:
            result = breakdown_service.explain(cleaned, req.focus)
            return result
        except Exception as e2:
            LOGGER.exception("Retry failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e2))


@gpt_router.post("/custom_breakdown", response_model=BreakdownResponse)
async def custom_breakdown(
    req: CustomBreakdownRequest,
    profile_id: Optional[str] = Depends(get_profile_id_optional)
) -> BreakdownResponse:
    """
    POST endpoint for analysing a Japanese sentence with custom system message
    and prompt.

    Args:
      req (CustomBreakdownRequest): JSON request matching
                                    `CustomBreakdownRequest` model.
      profile_id (str, optional): Profile ID Header.

    Returns:
      dict: Dictionary containing fields of `BreakdownResonse` model.

    Raises:
      HTTPException: Status code 500 if breakdown fails.
    """
    LOGGER.info((
        f"Custom Breakdown Request: sentence='{req.sentence!r}';"
        f"focus='{req.focus!r}' sysMsg='{req.sysMsg!r}'"
        f"prompt='{req.prompt!r}' version='{req.version!r}'")
                )
    try:
        result = breakdown_service.explain_custom(req.sentence,
                                                  req.sysMsg,
                                                  req.prompt,
                                                  req.version,
                                                  req.focus
                                                  )
        return result
    except Exception as e:
        LOGGER.warning(f"Custom Breakdown Failed: '{e}'")
        cleaned = re.sub(r"[（）]", "", req.sentence).strip().strip("\n")
        LOGGER.info(f"Retrying with clean sentence: '{cleaned!r}'")
        try:
            result = breakdown_service.explain_custom(cleaned,
                                                      req.sysMsg,
                                                      req.prompt,
                                                      req.version,
                                                      req.focus
                                                      )
            return result
        except Exception as e2:
            LOGGER.exception("Retry failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e2))


@gpt_router.get("/explain",)
async def explain_sentence(
    sentence: str = Query(...)
) -> Dict:
    """
    GET endpoint for analysing a Japanese sentence without a focus word.

    Args:
      sentence (str): Sentence to breakdown

    Returns:
      dict: Dictionary containing fields 'sentence' and 'explanation'

    Raises:
      HTTPException: Status code 500 if breakdown fails.
    """
    try:
        txt = breakdown_service.gpt_explainer.explain_sentence(sentence)
        return {"sentence": sentence, "explanation": txt}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@gpt_router.post("/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """
    POST endpoint for streaming an OpenAI API call response.

    Args:
      req (ChatRequest): JSON request containing fields of `ChatRequest` model.

    Returns:
      StreamingResponse: Stream of the model's response

    Raises:
      HTTPException: Status code 500 if call fails.
    """
    try:
        return StreamingResponse(sse_gen(req.model,
                                         req.system_message,
                                         req.prompt),
                                 media_type="text/event-stream"
                                 )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
