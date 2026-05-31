"""
This module defines the `dict_router` of the Mirumoji API

Attributes:
    LOGGER (logging.Logger): Module's logging object
    dict_router (APIRouter): The FastAPI router object
"""

import asyncio
import logging

from fastapi import APIRouter, Query

from ..models.jpdict import JapaneseWord, KotobaseData
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
    Tokenizes a sentence into words enriched with their dictionary data

    Args:
        sentence (str): The Japanese sentence to tokenize

    Returns:
        A list of `JapaneseWord` models, one per token

    Raises:
        FugashiError: If tokenization fails
        KotobaseError: If a dictionary lookup fails
    """
    return await asyncio.to_thread(text.process_sentence, sentence)
