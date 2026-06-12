"""
This module defines the `dict_router` of the Mirumoji API

Attributes:
    LOGGER (logging.Logger): Module's logging object
    dict_router (APIRouter): The FastAPI router object
"""

import asyncio
import logging

from fastapi import APIRouter, Query

from ..models.jpdict import (
    EnrichedJapaneseWord,
    JapaneseWord,
    KotobaseData,
)
from ..models.requests import TokenizeBatchRequest
from ..processing import text

LOGGER = logging.getLogger(__name__)
dict_router = APIRouter(prefix="/dict")


@dict_router.get("/query", response_model=KotobaseData)
async def query(
    word: str = Query(...),
    wildcard: bool = Query(False),
) -> KotobaseData:
    """
    Looks up dictionary data for a single word or a wildcard pattern

    Args:
        word (str): Word or wildcard pattern to look up
        wildcard (bool): When `True`, treat `word` as a wildcard pattern
            matching multiple words

    Returns:
        The `KotobaseData` for the query

    Raises:
        KotobaseError: If the lookup fails
    """
    return await asyncio.to_thread(
        text.query_kotobase,
        word,
        wildcard=wildcard,
    )


@dict_router.get("/tokenize", response_model=list[JapaneseWord])
async def tokenize(sentence: str = Query(...)) -> list[JapaneseWord]:
    """
    Tokenizes a sentence into useful, stitched words (no dictionary lookups)

    This is the fast path for rendering clickable text. Call `/dict/analyze`
    or `/dict/query` to fetch dictionary data for a word

    Args:
        sentence (str): The Japanese sentence to tokenize

    Returns:
        A list of `JapaneseWord` models, one per stitched word

    Raises:
        FugashiError: If tokenization fails
    """
    return await asyncio.to_thread(text.segment, sentence)


@dict_router.post("/tokenize", response_model=list[list[JapaneseWord]])
async def tokenize_batch(
    req: TokenizeBatchRequest,
) -> list[list[JapaneseWord]]:
    """
    Tokenizes many sentences in one request (stitched words, no dict data)

    Lets a client tokenize a whole subtitle file up front in a single call, so
    playback never tokenizes per-cue

    Args:
        req (TokenizeBatchRequest): The sentences to tokenize

    Returns:
        One `JapaneseWord` list per input sentence, in the same order

    Raises:
        FugashiError: If tokenization fails
    """
    return await asyncio.to_thread(text.segment_batch, req.sentences)


@dict_router.get("/analyze", response_model=list[EnrichedJapaneseWord])
async def analyze(
    sentence: str = Query(...),
) -> list[EnrichedJapaneseWord]:
    """
    Tokenizes a sentence and enriches every stitched word with dictionary data

    Slower than `/dict/tokenize` (one dictionary lookup per word). Intended for
    on-demand analysis rather than bulk rendering

    Args:
        sentence (str): The Japanese sentence to analyze

    Returns:
        A list of `EnrichedJapaneseWord` models, one per stitched word

    Raises:
        FugashiError: If tokenization fails
        KotobaseError: If a dictionary lookup fails
    """
    return await asyncio.to_thread(text.enrich, sentence)
