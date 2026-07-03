"""
This module defines the `dict_router` of the Mirumoji API

Attributes:
    LOGGER (logging.Logger): Module's logging object
    dict_router (APIRouter): The FastAPI router object
"""

import asyncio
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from fastapi.responses import Response

from ..models.jpdict import (
    BundleMode,
    EnrichedJapaneseWord,
    Example,
    JapaneseWord,
    JMEntry,
    KanjiAudio,
    KanjiInfo,
    KotobaseData,
    RadicalInfo,
)
from ..models.requests import TokenizeBatchRequest
from ..processing import text

LOGGER = logging.getLogger(__name__)
dict_router = APIRouter(prefix="/dict")

AUDIO_MEDIA_TYPES = {
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
}
"""
Maps a pronunciation clip's container format to its HTTP media type
"""


@dict_router.get("/query", response_model=KotobaseData)
async def query(
    word: Annotated[str, Query()],
    wildcard: Annotated[bool, Query()] = False,
    reading: Annotated[str | None, Query()] = None,
    pos: Annotated[str | None, Query()] = None,
) -> KotobaseData:
    """
    Looks up dictionary data for a single word or a wildcard pattern

    info: Token Hints
        - `reading` and `pos` are optional hints from tokenization

        - When provided, entries whose kana form matches the reading and whose
          part of speech matches the token rank first

        - Unknown written forms fall back to a lookup by reading

    Args:
        word (str): Word or wildcard pattern to look up
        wildcard (bool): When `True`, treat `word` as a wildcard pattern
            matching multiple words
        reading (str | None): The token's reading (any kana), when known
        pos (str | None): The token's UniDic top-level part of speech, when
            known

    Returns:
        The `KotobaseData` for the query

    Raises:
        KotobaseError: If the lookup fails
    """
    return await asyncio.to_thread(
        text.query_kotobase,
        word,
        wildcard=wildcard,
        reading=reading,
        pos=pos,
    )


@dict_router.get("/tokenize", response_model=list[JapaneseWord])
async def tokenize(
    sentence: Annotated[str, Query()],
    mode: Annotated[BundleMode, Query()] = BundleMode.grammar,
) -> list[JapaneseWord]:
    """
    Tokenizes a sentence into useful, stitched words (no dictionary lookups)

    This is the fast path for rendering clickable text. Call `/dict/analyze`
    or `/dict/query` to fetch dictionary data for a word

    Args:
        sentence (str): The Japanese sentence to tokenize
        mode (BundleMode): How aggressively to group tokens into words

    Returns:
        A list of `JapaneseWord` models, one per stitched word

    Raises:
        FugashiError: If tokenization fails
    """
    return await asyncio.to_thread(text.segment, sentence, mode)


@dict_router.post("/tokenize", response_model=list[list[JapaneseWord]])
async def tokenize_batch(
    req: Annotated[TokenizeBatchRequest, Body()],
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
    return await asyncio.to_thread(text.segment_batch, req.sentences, req.mode)


@dict_router.get("/analyze", response_model=list[EnrichedJapaneseWord])
async def analyze(
    sentence: Annotated[str, Query()],
    mode: Annotated[BundleMode, Query()] = BundleMode.grammar,
) -> list[EnrichedJapaneseWord]:
    """
    Tokenizes a sentence and enriches every stitched word with dictionary data

    Slower than `/dict/tokenize` (one dictionary lookup per word). Intended for
    on-demand analysis rather than bulk rendering

    Args:
        sentence (str): The Japanese sentence to analyze
        mode (BundleMode): How aggressively to group tokens into words

    Returns:
        A list of `EnrichedJapaneseWord` models, one per stitched word

    Raises:
        FugashiError: If tokenization fails
        KotobaseError: If a dictionary lookup fails
    """
    return await asyncio.to_thread(text.enrich, sentence, mode)


# --- Kanji Study ---


@dict_router.get("/kanji/{literal}", response_model=KanjiInfo)
async def kanji(literal: Annotated[str, Path()]) -> KanjiInfo:
    """
    Fetches the full profile of a single Kanji

    Args:
        literal (str): The Kanji literal

    Returns:
        The `KanjiInfo` profile

    Raises:
        HTTPException: 404 when the Kanji is unknown
        KotobaseError: If the lookup fails
    """
    info = await asyncio.to_thread(text.get_kanji, literal)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown Kanji '{literal}'",
        )
    return info


@dict_router.get("/kanji/{literal}/strokes")
async def kanji_strokes(literal: Annotated[str, Path()]) -> Response:
    """
    Fetches a Kanji's stroke-order diagram as an SVG document (`KanjiVG`)

    The SVG is self-contained, so the frontend can inline it and animate the
    stroke paths

    Args:
        literal (str): The Kanji literal

    Returns:
        The SVG document as `image/svg+xml`

    Raises:
        HTTPException: 404 when no stroke-order data exists for the Kanji
        KotobaseError: If the lookup fails
    """
    svg = await asyncio.to_thread(text.get_stroke_svg, literal)
    if svg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Stroke Order Data For '{literal}'",
        )
    return Response(content=svg, media_type="image/svg+xml")


@dict_router.get("/kanji/{literal}/audio", response_model=KanjiAudio)
async def kanji_audio(literal: Annotated[str, Path()]) -> KanjiAudio:
    """
    Lists the pronunciation clips available for a Kanji (`Kanji Alive`)

    The clips list is empty when the audio pack is not installed or the Kanji
    has no recorded clips

    Args:
        literal (str): The Kanji literal

    Returns:
        The `KanjiAudio` clip listing

    Raises:
        KotobaseError: If the lookup fails
    """
    return await asyncio.to_thread(text.get_kanji_audio, literal)


@dict_router.get("/kanji/{literal}/audio/clip")
async def kanji_audio_clip(
    literal: Annotated[str, Path()],
    clip: Annotated[str, Query()],
) -> Response:
    """
    Streams the raw bytes of one pronunciation clip

    Args:
        literal (str): The Kanji literal the clip belongs to
        clip (str): The clip id from the audio listing endpoint

    Returns:
        The audio bytes with the clip's media type

    Raises:
        HTTPException: 404 when no clip matches
        KotobaseError: If the lookup fails
    """
    payload = await asyncio.to_thread(text.get_audio_clip, literal, clip)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Audio Clip '{clip}' For '{literal}'",
        )
    name, data = payload
    ext = name.rsplit(".", 1)[-1].lower()
    return Response(
        content=data,
        media_type=AUDIO_MEDIA_TYPES.get(ext, "application/octet-stream"),
    )


@dict_router.get("/kanji/{literal}/words", response_model=list[JMEntry])
async def kanji_words(
    literal: Annotated[str, Path()],
    limit: Annotated[int, Query(ge=1)] = 50,
) -> list[JMEntry]:
    """
    Lists dictionary entries whose written form uses a Kanji

    Args:
        literal (str): The Kanji literal
        limit (int): Maximum number of entries to return

    Returns:
        The matching `JMEntry` models

    Raises:
        KotobaseError: If the lookup fails
    """
    return await asyncio.to_thread(text.get_words_with_kanji, literal, limit)


@dict_router.get("/kanji/{literal}/sentences", response_model=list[Example])
async def kanji_sentences(
    literal: Annotated[str, Path()],
    limit: Annotated[int, Query(ge=1)] = 10,
) -> list[Example]:
    """
    Lists example sentences that contain a Kanji

    Args:
        literal (str): The Kanji literal
        limit (int): Maximum number of sentences to return

    Returns:
        The matching `Example` sentences with translations

    Raises:
        KotobaseError: If the lookup fails
    """
    return await asyncio.to_thread(
        text.get_sentences_with_kanji,
        literal,
        limit,
    )


# --- Search ---


@dict_router.get("/search", response_model=list[JMEntry])
async def search(
    q: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1)] = 50,
) -> list[JMEntry]:
    """
    Searches dictionary entries by English meaning (reverse lookup)

    Japanese word and wildcard searches go through `/dict/query` instead

    Args:
        q (str): The English search text
        limit (int): Maximum number of entries to return

    Returns:
        The matching `JMEntry` models

    Raises:
        KotobaseError: If the search fails
    """
    return await asyncio.to_thread(text.search_english, q, limit)


@dict_router.get("/resolve", response_model=list[JMEntry])
async def resolve(ref: Annotated[str, Query(min_length=1)]) -> list[JMEntry]:
    """
    Resolves a sense cross-reference or antonym code into its entries

    Args:
        ref (str): The reference code from a sense's `xrefs` or `antonyms`

    Returns:
        The referenced `JMEntry` models

    Raises:
        KotobaseError: If the resolution fails
    """
    return await asyncio.to_thread(text.resolve_reference, ref)


# --- Radicals ---


@dict_router.get("/radicals", response_model=list[RadicalInfo])
async def radicals() -> list[RadicalInfo]:
    """
    Lists every search radical with its stroke count (`RADKFILE`)

    Returns:
        All search radicals

    Raises:
        KotobaseError: If the lookup fails
    """
    return await asyncio.to_thread(text.list_radicals)


@dict_router.get("/by-radicals", response_model=list[KanjiInfo])
async def by_radicals(
    radicals: Annotated[str, Query(min_length=1)],
    mode: Annotated[Literal["all", "any"], Query()] = "all",
) -> list[KanjiInfo]:
    """
    Finds Kanji that contain one, or every one of the given radicals

    Args:
        radicals (str): The radical glyphs, concatenated or comma-separated
            (e.g. `言口` or `言,口`)
        mode (Literal): When `all`, every one of `radicals` must be present in
            the kanji. When `any`, kanjis that contain at least one of
            `radicals` are matched

    Returns:
        The matching `KanjiInfo` models

    Raises:
        HTTPException: 400 when no radical glyphs are provided
        KotobaseError: If the search fails
    """
    glyphs = tuple(ch for ch in radicals if ch != ",")
    if not glyphs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Radicals Provided",
        )
    return await asyncio.to_thread(
        text.kanji_by_radicals,
        radicals=glyphs,
        match=mode,
    )
