"""
Defines custom ASGI middleware for the FastAPI application
"""

import logging
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..log import REQUEST_CONTEXT

LOGGER = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    Pure-ASGI middleware that binds a request context and logs a summary line

    info: What It Does
        - Assigns each HTTP request a short correlation id and records its
          `method`, `path`, `client ip`, and `query string` into
          `REQUEST_CONTEXT`, so every log line emitted while the request is
          handled can be tied back to it

        - Emits one request-summary line per request, replacing uvicorn's
          silenced access log

    question: Why Pure ASGI
        - This is implemented as a pure-ASGI middleware (not
          `BaseHTTPMiddleware`) so that it never reads or buffers the request
          body

        - The streaming upload routes and the Server-Sent-Events endpoints
          therefore pass through untouched

    info: Operations Per Request
        - Builds the request context (`correlation id` + `method` + `path` +
          `client ip` + `query parameters`)

        - Stores it in `REQUEST_CONTEXT`, keeping the reset token so the
          previous context is restored after

        - Wraps the ASGI `send` channel to capture the response status from
          the `http.response.start` message, without touching the body

        - Always logs a single summary line and resets the context, even when
          the wrapped app raises
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Constructs an instance and binds the ASGI app to it

        Args:
            app (ASGIApp): The downstream ASGI application to wrap
        """
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """
        Binds the request context for HTTP scopes and logs the summary

        Non-HTTP scopes (`lifespan`, `websocket`) pass straight through with no
        context and no summary line

        Args:
            scope (Scope): The ASGI connection scope
            receive (Receive): The ASGI receive channel, forwarded untouched
            send (Send): The ASGI send channel, wrapped to read the status
        """

        # Let Lifespan + Websocket Scopes Pass Through
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract Request Metadata
        method = scope.get("method", "")
        path = scope.get("path", "")
        client = scope.get("client")
        query = scope.get("query_string", b"").decode("latin-1")

        # `scope["client"]` Is A `(host, port)` Tuple, Or `None` Behind A
        # Transport That Doesn't Expose The Peer
        client_ip = f"{client[0]}:{client[1]}" if client else ""

        context = {
            "correlation_id": uuid.uuid4().hex,
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "query": query,
        }

        # Set `REQUEST_CONTEXT`
        token = REQUEST_CONTEXT.set(context)

        status = 0

        async def send_wrapper(message: Message) -> None:
            # Capture the status code received by the client from the
            # response-start message so that the summary line can report it
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        # Time The Request
        start = time.perf_counter()
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            # The logging setup takes over all logging configuration, so log
            # the tagged traceback of an unhandled error here. FastAPI has
            # already sent a 500 through send_wrapper, so the error is not
            # re-raised, since doing so would only make the server log
            # a second, untagged copy of the same traceback
            LOGGER.exception(f"Unhandled Error During {method} {path}")
        finally:
            # Runs on both success and on failure, so the context never leaks
            # into the next request served on this task
            elapsed_ms = (time.perf_counter() - start) * 1000
            LOGGER.info(f"{method} {path} {status} In {elapsed_ms:.0f}ms")
            REQUEST_CONTEXT.reset(token)
