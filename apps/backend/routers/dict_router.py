"""
This module defines the `dict_router` of the Mirumoji API.

Attributes:
  LOGGER (logging.Logger): Router Logging Object.
  dict_router (APIRouter): The FastAPI Router object.

"""

from fastapi import APIRouter, Query, HTTPException
import logging
from processing.Processor import Processor
from utils.env_utils import using_modal
from models.DictLookup import DictLookup
from models.DictWildcardLookup import DictWildcardLookup

USING_MODAL = using_modal()
LOGGER = logging.getLogger(__name__)
dict_router = APIRouter(prefix="/dict")
processor = Processor(use_modal=USING_MODAL)
breakdown_service = processor.sentence_breakdown_service


@dict_router.get("/sentence_lookup")
async def explain_sentence(sentence: str = Query(...)) -> dict:
    """
    Endpoint returning enriched tokens without gpt explanation.

    Args:
      sentence (str): Sentence to return tokens from.

    Returns:
      dict: Dictionary containg 'sentence' and 'tokens' fields.

    Raises:
      HTTPException: If lookup fails.
    """
    try:
        tokens = breakdown_service.word_lookup(sentence)
        return {"sentence": sentence, "tokens": tokens}

    except Exception as e:
        LOGGER.exception(f"Failed to breakdown sentence '{sentence}'")
        raise HTTPException(status_code=500, detail=str(e))


@dict_router.get("/word", response_model=DictLookup)
async def query_word(word: str = Query(...)) -> DictLookup:
    """
    Endpoint returning dictionary information for a single word

    Args:
      word (str): Sentence to return tokens from.

    Returns:
      DictLookup: Pydantic Model containing word information

    Raises:
      HTTPException: If lookup fails.
    """
    try:
        r = breakdown_service.single_word_lookup(word)
        return r
    except Exception as e:
        LOGGER.exception(f"Failed to query kotobase for word: '{word}'")
        raise HTTPException(status_code=500,
                            detail=str(e)
                            )


@dict_router.get("/wildcard", response_model=DictWildcardLookup)
async def wildcard_query(pattern: str = Query(...)) -> DictWildcardLookup:
    """
    Endpoint returning dictionary information for a wildcard pattern lookup

    Args:
      pattern (str): Sentence to return tokens from.

    Returns:
      DictWildcardLookup: Pydantic Model containing wildcard pattern lookup
                          information

    Raises:
      HTTPException: If lookup fails.
    """
    try:
        # Append final wildcard if wildcard marker not present
        if ("%" not in pattern) or ("*" not in pattern):
            pattern += "*"
        r = breakdown_service.wildcard_lookup(pattern)
        return r
    except Exception as e:
        LOGGER.exception(
            f"Failed to query kotobase for wildcard pattern: '{pattern}'"
            )
        raise HTTPException(status_code=500,
                            detail=str(e)
                            )
