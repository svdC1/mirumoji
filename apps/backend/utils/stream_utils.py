"""
This module defines helper functions for handling streaming responses
for fastapi's endpoints.

Attributes:
  LOGGER (logging.Logger): Module's logger object.
"""

from typing import (Union,
                    Iterator,
                    Generator,
                    Any)
from processing.gpt_wrapper import GptModel
import logging
from pathlib import Path
import asyncio
from fastapi import HTTPException
from typing import Callable
from fastapi.responses import StreamingResponse

LOGGER = logging.getLogger(__name__)


def _generate_reply(version: str,
                    sys_msg: str,
                    prompt: str
                    ) -> Union[Iterator[str],
                               None]:
    """
    Stream reply from a `GptModel` object OpenAI API call.

    Args:
      version (str): The OpenAI GPT model version to use.
      sys_msg (str): The system message to use for the model.
      prompt (str): User prompt for the model.

    Yields:
      Union[Iterator[str], None]: The text chunks from the reply.
    """
    try:
        model = GptModel(
                version=version,
                system_msg=sys_msg)
        for chunk in model.stream_request(prompt):
            yield chunk
    except Exception as e:
        LOGGER.error(str(e))
        return None


def sse_gen(version: str,
            system_message: str,
            prompt: str
            ) -> Generator[str, Any, None]:
    """
    Stream reply from a `GptModel` object OpenAI API call.

    Args:
      version (str): The OpenAI GPT model version to use.
      system_message (str): The system message to use for the model.
      prompt (str): User prompt for the model.

    Yields:
      Generator[str, Any, None]: The text chunks from the reply.
    """
    reply = _generate_reply(version,
                            system_message,
                            prompt)

    if not reply:
        LOGGER.error("Failed to generate stream")
        raise HTTPException(400, "Failed to generate stream")
    for chunk in reply:
        yield f"data: {chunk}\n\n"
    yield "event: done\ndata:\n\n"


def stream_response_with_task(
    path: Path,
    task_func: Callable[[], None],
    filename: str,
    media_type: str | None = None,
    keepalive_interval: float = 20.0
) -> StreamingResponse:
    """
    Streams a long‐running task’s output file over HTTP without timing out
    by running `task_func` in a background thread while yielding a space
    every `keepalive_interval` seconds to keep proxies alive.
    Args:
      path (pathlib.Path): The path to the function's resulting file.
      task_func (Callable[[], None]): The function which generates the file.
      filename (str): Filename to pass to response header.
      media_type (str, optional): Optional media type to pass to response
                                  header.
      keepalive_interval (float): Interval between spaces yielded in seconds.

    Returns:
      StreamReponse: Once the task is done, streams the file at `path` in 8k
                     chunks.
    """
    async def _generator():
        task = asyncio.create_task(asyncio.to_thread(task_func))
        while not task.done():
            await asyncio.sleep(keepalive_interval)
            yield b" "
        await task

        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                yield chunk
        return

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return StreamingResponse(
        _generator(),
        media_type=media_type,
        headers=headers
    )
