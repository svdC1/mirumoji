# gpt_router.py
import logging
import re
import time
from fastapi import (APIRouter,
                     Query,
                     HTTPException,
                     Depends,
                     status)
from fastapi.responses import StreamingResponse
from typing import Optional

from processing.Processor import Processor
from models.ChatRequest import ChatRequest
from models.BreakdownRequest import BreakdownRequest
from models.BreakdownResponse import BreakdownResponse
from models.CustomBreakdownRequest import CustomBreakdownRequest
from utils.stream_utils import sse_gen
from profile_manager import get_profile_id_optional
from utils.env_utils import using_modal

USING_MODAL = using_modal()
logger = logging.getLogger(__name__)

processor = Processor(use_modal=USING_MODAL)
breakdown_service = processor.sentence_breakdown_service

gpt_router = APIRouter(prefix='/gpt')


@gpt_router.post("/breakdown", response_model=BreakdownResponse)
async def breakdown(
    req: BreakdownRequest,
    profile_id: Optional[str] = Depends(get_profile_id_optional)
):
    log_prefix = f"[Profile: {profile_id}] " if profile_id else ""
    logger.info(f"{log_prefix}Breakdown Request: \
        sentence={req.sentence!r} focus={req.focus!r}")
    try:
        t0 = time.perf_counter()
        result = breakdown_service.explain(req.sentence, req.focus)
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(f"{log_prefix}Request Time: {elapsed:.1f} ms")
        return result
    except Exception as e:
        logger.warning(f"{log_prefix}Breakdown Failed: {e}")
        cleaned = re.sub(r"[（）]", "", req.sentence)
        logger.info(f"{log_prefix}Retrying with clean sentence: {cleaned!r}")
        try:
            t0 = time.perf_counter()
            result = breakdown_service.explain(cleaned, req.focus)
            elapsed = (time.perf_counter() - t0) * 1000
            logger.info(f"{log_prefix}Retry Request Time: {elapsed:.1f} ms")
            result_dict = result if isinstance(result, dict) \
                else result.model_dump()
            result_dict["sentence"] = req.sentence
            return result_dict
        except Exception as e2:
            logger.exception(f"{log_prefix}Retry failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e2))


@gpt_router.post("/custom_breakdown", response_model=BreakdownResponse)
async def custom_breakdown(
    req: CustomBreakdownRequest,
    profile_id: Optional[str] = Depends(get_profile_id_optional)
):
    log_prefix = f"[Profile: {profile_id}] " if profile_id else ""
    logger.info(
        f"{log_prefix}Custom Breakdown Request: sentence={req.sentence!r} \
            focus={req.focus!r} sysMsg={req.sysMsg!r} prompt={req.prompt!r}")
    try:
        t0 = time.perf_counter()
        result = breakdown_service.explain_custom(req.sentence, req.sysMsg,
                                                  req.prompt, req.focus)
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(f"{log_prefix}Request Time: {elapsed:.1f} ms")
        return result
    except Exception as e:
        logger.warning(f"{log_prefix}Custom Breakdown Failed: {e}")
        cleaned = re.sub(r"[（）]", "", req.sentence)
        logger.info(f"{log_prefix}Retrying with clean sentence: {cleaned!r}")
        try:
            t0 = time.perf_counter()
            result = breakdown_service.explain_custom(cleaned, req.sysMsg,
                                                      req.prompt, req.focus)
            elapsed = (time.perf_counter() - t0) * 1000
            logger.info(f"{log_prefix}Retry Request Time: {elapsed:.1f} ms")
            result_dict = result if isinstance(result, dict) \
                else result.model_dump()
            result_dict["sentence"] = req.sentence
            return result_dict
        except Exception as e2:
            logger.exception(f"{log_prefix}Retry failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e2))


@gpt_router.get(
    "/explain",
    summary="Cure Dolly–style full sentence explanation",
)
async def explain_sentence(
    sentence: str = Query(..., description="Japanese sentence to explain")
):
    try:
        txt = breakdown_service.gpt_explainer.explain_sentence(sentence)
        return {"sentence": sentence, "explanation": txt}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@gpt_router.post("/stream")
async def chat_stream(req: ChatRequest):
    try:
        return StreamingResponse(sse_gen(req.model, req.system_message,
                                         req.prompt),
                                 media_type="text/event-stream")
    except Exception as e:
        # Consider standardizing error response here too
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
