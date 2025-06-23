"""
This module defines the `dict_router` of the API.

Attributes:
  USING_MODAL (bool): Wether using MODAL or not.
  LOGGER (logging.Logger): Router Logging Object.

"""

from fastapi import APIRouter, Query, HTTPException
import logging
from processing.Processor import Processor
from utils.env_utils import using_modal

USING_MODAL = using_modal()
LOGGER = logging.getLogger(__name__)
dict_router = APIRouter(prefix="/dict")
processor = Processor(use_modal=USING_MODAL)
breakdown_service = processor.sentence_breakdown_service


@dict_router.get("/sentence_lookup")
async def explain_sentence(sentence: str = Query(...)):
    """
    Endpoint returning enriched tokens without gpt explanation.

    Args:
      sentence (string): Sentence to return tokens from.

    Raises:
      HTTPException
    """
    try:
        tokens = breakdown_service.word_lookup(sentence)
        return {"sentence": sentence, "tokens": tokens}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
