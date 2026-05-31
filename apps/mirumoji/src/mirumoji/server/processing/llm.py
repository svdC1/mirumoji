"""
Provider-Agnostic LLM Layer

Exposes a thin `LLMClient` protocol with an `OpenAI-Compatible` adapter and a
dedicated Anthropic adapter

tip: Model Selection
    - Model selection uses a `provider:model` string
      (e.g. `"openai:gpt-4.1-mini"`)

    - Which providers are usable in a given deployment is detected from
      installed SDKs and configured environment variables, so requesting an
      unconfigured provider raises a domain exception

"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Protocol

from anthropic import Anthropic
from openai import OpenAI

from ...exceptions import (
    InvalidModelStringError,
    LLMProviderUnavailableError,
    LLMRequestError,
)
from ..config import env_present, get_settings

LOGGER = logging.getLogger(__name__)

# Anthropic's Messages API requires an explicit token cap
# 4096 is generous enough for both short breakdowns and longer SRT fixes
DEFAULT_MAX_TOKENS = 4096

# Gemini's OpenAI-Compatible Endpoint
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class LLMProvider(str, Enum):
    """
    Enum listing all supported LLM providers

    `gemini` and `local` are served through the OpenAI-compatible adapter while
    `anthropic` uses the native SDK
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"


# --- Client protocol + adapters ---


class LLMClient(Protocol):
    """
    Protocol defining the minimal adapter surface required by the server for
    LLM calls
    """

    def complete(self, *, system: str, prompt: str, model: str) -> str:
        """
        Returns the full completion text for a single prompt
        """
        ...

    def stream(
        self,
        *,
        system: str,
        prompt: str,
        model: str,
    ) -> Iterator[str]:
        """
        Yields completion text chunks as they arrive
        """
        ...


class OpenAICompatClient:
    """
    Adapter for the OpenAI SDK pointed at any OpenAI-compatible endpoint via
    `base_url`. Covers the following providers.

    - `OpenAI`
    - `Gemini` (OpenAI-Compatible Endpoint)
    - `Local` (Any Local OpenAI-Compatible LLM Server)
    - `Modal-Hosted (Any OpenAI-Compatible LLM Server Running In a Modal
      Container)

    Args:
        base_url (str | None): Endpoint base URL; `None` uses OpenAI's default
        api_key (str): API key (use a non-empty placeholder for local servers
            that don't authenticate)
    """

    def __init__(self, *, base_url: str | None, api_key: str) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, *, system: str, prompt: str, model: str) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise LLMRequestError(f"LLM request failed: {e}") from e

    def stream(
        self,
        *,
        system: str,
        prompt: str,
        model: str,
    ) -> Iterator[str]:
        try:
            stream = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )
            for chunk in stream:
                text = chunk.choices[0].delta.content or ""
                if text:
                    yield text
        except Exception as e:
            raise LLMRequestError(f"LLM stream failed: {e}") from e


class AnthropicClient:
    """
    `LLMClient` backed by the native Anthropic Messages API

    Args:
        api_key (str): Anthropic API key
    """

    def __init__(self, *, api_key: str) -> None:
        self._client = Anthropic(api_key=api_key)

    def complete(self, *, system: str, prompt: str, model: str) -> str:
        try:
            msg = self._client.messages.create(
                model=model,
                system=system,
                max_tokens=DEFAULT_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(
                block.text
                for block in msg.content
                if getattr(block, "type", None) == "text"
            )
        except Exception as e:
            raise LLMRequestError(f"LLM request failed: {e}") from e

    def stream(
        self,
        *,
        system: str,
        prompt: str,
        model: str,
    ) -> Iterator[str]:
        try:
            with self._client.messages.stream(
                model=model,
                system=system,
                max_tokens=DEFAULT_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                yield from stream.text_stream
        except Exception as e:
            raise LLMRequestError(f"LLM stream failed: {e}") from e


# --- Provider Registry + Detection ---


@dataclass(frozen=True)
class LLMProviderSpec:
    """
    Describes how to detect and build an LLM provider's client

    Args:
        kind (str): `openai_compat` or `anthropic`
        module (str): Importable SDK module the provider needs
        key_env (str | None): Env variable holding the API key, if any
        key_required (bool): Whether `key_env` must be set for availability
        base_url (str | None): Static base URL for the OpenAI-compatible
            adapter
        base_url_env (str | None): Env var holding the base URL (for `local`)
    """

    kind: str
    module: str
    key_env: str | None
    key_required: bool
    base_url: str | None = None
    base_url_env: str | None = None


LLM_PROVIDER_REGISTRY: dict[LLMProvider, LLMProviderSpec] = {
    LLMProvider.OPENAI: LLMProviderSpec(
        kind="openai_compat",
        module="openai",
        key_env="OPENAI_API_KEY",
        key_required=True,
    ),
    LLMProvider.GEMINI: LLMProviderSpec(
        kind="openai_compat",
        module="openai",
        key_env="GEMINI_API_KEY",
        key_required=True,
        base_url=GEMINI_BASE_URL,
    ),
    LLMProvider.ANTHROPIC: LLMProviderSpec(
        kind="anthropic",
        module="anthropic",
        key_env="ANTHROPIC_API_KEY",
        key_required=True,
    ),
    LLMProvider.LOCAL: LLMProviderSpec(
        kind="openai_compat",
        module="openai",
        key_env="MIRUMOJI_LLM_API_KEY",
        key_required=False,
        base_url_env="MIRUMOJI_LLM_BASE_URL",
    ),
}


def parse_model(selector: str) -> tuple[LLMProvider, str]:
    """
    Parse a `provider:model` selector

    Args:
        selector (str): e.g. `"openai:gpt-4.1-mini"`

    Returns:
        Tuple of the resolved `LLMProvider` and the bare model name

    Raises:
        InvalidModelStringError: If the selector is malformed or names an
            unknown LLMProvider
    """
    if ":" not in selector:
        raise InvalidModelStringError(
            f"Model selector must be 'provider:model', got '{selector}'",
        )
    prefix, _, model = selector.partition(":")
    prefix = prefix.strip().lower()
    model = model.strip()
    try:
        provider = LLMProvider(prefix)
    except ValueError:
        valid = ", ".join(p.value for p in LLMProvider)
        raise InvalidModelStringError(
            f"Unknown provider '{prefix}'; expected one of: {valid}",
        ) from None
    if not model:
        raise InvalidModelStringError(
            f"Empty model name in selector '{selector}'",
        )
    return provider, model


def provider_available(provider: LLMProvider) -> bool:
    """
    Whether an LLM provider is usable in this deployment

    A provider is available when its required environment variables
    (API key, base URL) are configured

    Args:
        provider (LLMProvider): LLM provider to check

    Returns:
        `True` if the LLM provider can be used
    """
    spec = LLM_PROVIDER_REGISTRY[provider]
    if spec.base_url_env and not env_present(spec.base_url_env):
        return False
    return not (
        (spec.key_required and spec.key_env) and not env_present(spec.key_env)
    )


def provider_status() -> list[dict]:
    """
    Report availability of every known LLM provider

    Returns:
        List of `{"provider": str, "available": bool}` for each provider, so
            the frontend can offer configured ones and grey out the rest
    """
    return [
        {"provider": p.value, "available": provider_available(p)}
        for p in LLMProvider
    ]


@lru_cache
def build_client(provider: LLMProvider) -> LLMClient:
    """
    Builds a client for an LLM provider, resolving its config from the
    environment

    Cached per provider so clients aren't rebuilt on every request. The
    environment is fixed for the server's lifetime

    Args:
        provider (LLMProvider): LLM provider to build a client for

    Returns:
        A ready `LLMClient`

    Raises:
        LLMProviderUnavailableError: If the provider's SDK or configuration
            is missing
    """
    if not provider_available(provider):
        raise LLMProviderUnavailableError(
            f"LLM provider '{provider.value}' is not available."
            f"Configure its environment variables to use it",
            details={"provider": provider.value},
        )
    spec = LLM_PROVIDER_REGISTRY[provider]
    api_key = os.environ.get(spec.key_env) if spec.key_env else None

    if spec.kind == "anthropic":
        return AnthropicClient(api_key=api_key or "")

    base_url = spec.base_url
    if spec.base_url_env:
        base_url = os.environ.get(spec.base_url_env)

    # OpenAI SDK requires a non-empty key string even when the upstream
    # (e.g. a local server) ignores it
    return OpenAICompatClient(
        base_url=base_url, api_key=api_key or "not-needed"
    )


def client_for_model(selector: str) -> tuple[LLMClient, str]:
    """
    Resolve a `"provider:model"` selector to a client and bare model name

    Args:
        selector (str): e.g. `"anthropic:claude-sonnet-4-6"`

    Returns:
        Tuple of the built `LLMClient` and the bare model name

    Raises:
        InvalidModelStringError: If the selector is malformed
        LLMProviderUnavailableError: If the provider is unavailable
    """
    provider, model = parse_model(selector)
    return build_client(provider), model


# --- Prompt Builders ---


def default_breakdown_prompt(sentence: str, focus: str) -> tuple[str, str]:
    """
    Build the (system, prompt) pair for the default word-nuance breakdown

    Args:
        sentence (str): Full Japanese sentence
        focus (str): Target word to explain in context

    Returns:
        Tuple of the system message and the user prompt
    """
    return (
        get_settings().breakdown_sys_msg,
        f"{sentence}. Explain usage of word : {focus}",
    )


def sentence_breakdown_prompt(sentence: str) -> tuple[str, str]:
    """
    Build the (system, prompt) pair for explaining a whole sentence

    Args:
        sentence (str): Full Japanese sentence

    Returns:
        Tuple of the system message and the user prompt
    """
    return (
        get_settings().breakdown_sys_msg,
        f"Sentence : {sentence}. Word: None, explain the sentence.",
    )


def custom_breakdown_prompt(
    sentence: str,
    focus: str,
    system_message: str,
    prompt_template: str,
) -> tuple[str, str]:
    """
    Build the (system, prompt) pair for a profile's custom breakdown template

    Args:
        sentence (str): Full Japanese sentence
        focus (str): Target word to explain in context
        system_message (str): Custom system message
        prompt_template (str): Template using `{0}` = sentence, `{1}` = focus

    Returns:
        Tuple of the system message and the formatted user prompt

    Raises:
        LLMRequestError: If the template cannot be formatted
    """
    try:
        prompt = prompt_template.format(sentence, focus)
    except (IndexError, KeyError, ValueError) as e:
        raise LLMRequestError(
            f"Invalid custom prompt template: {e}",
        ) from e
    return system_message, prompt


def sse_format(chunks: Iterable[str]) -> Iterator[str]:
    """
    Wrap text chunks as Server-Sent Events, ending with a `done` event

    Args:
        chunks (Iterable[str]): Text chunks to emit

    Yields:
        SSE-formatted strings (`data: <chunk>\\n\\n`), then a terminal
            `event: done` frame
    """
    for chunk in chunks:
        yield f"data: {chunk}\n\n"
    yield "event: done\ndata:\n\n"
