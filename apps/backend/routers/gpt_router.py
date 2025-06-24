"""
This module defines the `gpt_router` of the Mirumoji API.

Attributes:
  LOGGER (logging.Logger): Module's Logging object.
  gpt_router (APIRouter): The FastAPI Router Object.
"""
import logging
import re
import time
from fastapi import (APIRouter,
                     Query,
                     HTTPException,
                     Depends,
                     status)
from fastapi.responses import StreamingResponse
from typing import Optional, Dict

from processing.Processor import Processor
from models.ChatRequest import ChatRequest
from models.BreakdownRequest import BreakdownRequest
from models.BreakdownResponse import BreakdownResponse
from models.CustomBreakdownRequest import CustomBreakdownRequest
from utils.stream_utils import sse_gen
from profile_manager import get_profile_id_optional
from utils.env_utils import using_modal

USING_MODAL = using_modal()
LOGGER = logging.getLogger(__name__)

processor = Processor(use_modal=USING_MODAL)
breakdown_service = processor.sentence_breakdown_service

gpt_router = APIRouter(prefix='/gpt')


@gpt_router.post("/breakdown", response_model=BreakdownResponse)
async def breakdown(
    req: BreakdownRequest,
    profile_id: Optional[str] = Depends(get_profile_id_optional)
) -> Dict:
    """
    POST endpoint for analysing a Japanese sentence.

    Args:
      req (BreakdownRequest): JSON request matching `BreakdownRequest` model.
      profile_id (str, optinoal): Profile ID Header.

    Returns:
      dict: Dictionary containing fields of `BreakdownResonse` model.

    Raises:
      HTTPException: Status code 500 if breakdown fails.
    """
    log_prefix = f"[Profile: {profile_id}] " if profile_id else ""
    LOGGER.info(f"{log_prefix}Breakdown Request: \
        sentence={req.sentence!r} focus={req.focus!r}")
    try:
        t0 = time.perf_counter()
        result = breakdown_service.explain(req.sentence, req.focus)
        elapsed = (time.perf_counter() - t0) * 1000
        LOGGER.info(f"{log_prefix}Request Time: {elapsed:.1f} ms")
        return result
    except Exception as e:
        LOGGER.warning(f"{log_prefix}Breakdown Failed: {e}")
        cleaned = re.sub(r"[（）]", "", req.sentence)
        LOGGER.info(f"{log_prefix}Retrying with clean sentence: {cleaned!r}")
        try:
            t0 = time.perf_counter()
            result = breakdown_service.explain(cleaned, req.focus)
            elapsed = (time.perf_counter() - t0) * 1000
            LOGGER.info(f"{log_prefix}Retry Request Time: {elapsed:.1f} ms")
            result_dict = result if isinstance(result, dict) \
                else result.model_dump()
            result_dict["sentence"] = req.sentence
            return result_dict
        except Exception as e2:
            LOGGER.exception(f"{log_prefix}Retry failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e2))


@gpt_router.post("/custom_breakdown", response_model=BreakdownResponse)
async def custom_breakdown(
    req: CustomBreakdownRequest,
    profile_id: Optional[str] = Depends(get_profile_id_optional)
) -> Dict:
    """
    POST endpoint for analysing a Japanese sentence with custom system message
    and prompt.

    Args:
      req (CustomBreakdownRequest): JSON request matching
                                    `CustomBreakdownRequest` model.
      profile_id (str, optinoal): Profile ID Header.

    Returns:
      dict: Dictionary containing fields of `BreakdownResonse` model.

    Raises:
      HTTPException: Status code 500 if breakdown fails.
    """
    log_prefix = f"[Profile: {profile_id}] " if profile_id else ""
    LOGGER.info(
        f"{log_prefix}Custom Breakdown Request: sentence={req.sentence!r} \
            focus={req.focus!r} sysMsg={req.sysMsg!r} prompt={req.prompt!r}")
    try:
        t0 = time.perf_counter()
        result = breakdown_service.explain_custom(req.sentence,
                                                  req.sysMsg,
                                                  req.prompt,
                                                  req.focus)
        elapsed = (time.perf_counter() - t0) * 1000
        LOGGER.info(f"{log_prefix}Request Time: {elapsed:.1f} ms")
        return result
    except Exception as e:
        LOGGER.warning(f"{log_prefix}Custom Breakdown Failed: {e}")
        cleaned = re.sub(r"[（）]", "", req.sentence)
        LOGGER.info(f"{log_prefix}Retrying with clean sentence: {cleaned!r}")
        try:
            t0 = time.perf_counter()
            result = breakdown_service.explain_custom(cleaned,
                                                      req.sysMsg,
                                                      req.prompt,
                                                      req.focus)
            elapsed = (time.perf_counter() - t0) * 1000
            LOGGER.info(f"{log_prefix}Retry Request Time: {elapsed:.1f} ms")
            result_dict = result if isinstance(result, dict) \
                else result.model_dump()
            result_dict["sentence"] = req.sentence
            return result_dict
        except Exception as e2:
            LOGGER.exception(f"{log_prefix}Retry failed")
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
