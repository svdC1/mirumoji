from typing import (Union,
                    Iterator)
from processing.gpt_wrapper import GptModel
import logging
from pathlib import Path
import asyncio
from fastapi import HTTPException
from typing import Callable
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


def generate_reply(version: str,
                   sys_msg: str,
                   prompt: str) -> Union[Iterator[str],
                                         None]:
    """Core streaming logic, yields chunks of text."""
    try:
        model = GptModel(
                version=version,
                system_msg=sys_msg)
        for chunk in model.stream_request(prompt):
            yield chunk
    except Exception as e:
        logger.error(str(e))
        return None


def sse_gen(version: str,
            system_message: str,
            prompt: str):
    reply = generate_reply(version,
                           system_message,
                           prompt)

    if not reply:
        logger.error("Failed to generate stream")
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
    Streams a long‐running task’s output file over HTTP without timing out.
    1) Runs task_func() in a background thread.
    2) Yields a single space every `keepalive_interval` seconds to
    keep proxies alive.
    3) Once the task is done, streams the file at `path` in 8k chunks.
    """
    async def _generator():
        # 1) launch the blocking work
        task = asyncio.create_task(asyncio.to_thread(task_func))

        # 2) keep the connection alive until task completes
        while not task.done():
            await asyncio.sleep(keepalive_interval)
            yield b" "

        # 3) propagate any exception from the task
        await task

        # 4) stream the real file
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
