"""
Defines an `HTTP Basic Auth` gate for the Modal-hosted app

question: Why Basic Auth
    - A browser can't attach Modal's proxy tokens to the initial page
      navigation, which is the usual way to protect modal-deployed web
      apps

    - Since the `mirumoji-hosted` FastAPI app serves a browser `SPA`,
      it is protected with `HTTP Basic Auth` instead

    - The browser prompts once and then sends the credentials on every
      request, so the whole app is gated without requiring implementation
      of auth tooling in the server and frontend

    - This is done so that the main app can remain free of authentication,
      since its primary usage is as a self-hosted app
"""

from __future__ import annotations

import base64
import hmac
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

# Define The ASGI Types To Avoid Importing Starlette
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class BasicAuthMiddleware:
    """
    Pure-ASGI middleware that gates every request behind `HTTP Basic Auth`

    info: Browser-Native
        - A `401` with a `WWW-Authenticate: Basic` header makes the browser
          show its own credential prompt and then send `Authorization: Basic`
          on every later request, including the top-level navigation

        - This needs no login page, session, or cookie, so the app and the
          frontend are unchanged

    info: Constant-Time
        The credentials are compared with `hmac.compare_digest`, so the check
        does not leak the password through timing
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        username: str,
        password: str,
        realm: str = "Mirumoji",
    ) -> None:
        """
        Sets up the `HTTP Basic Auth` token and challenge headers based
        on the provided arguments

        Args:
            app (ASGIApp): The application to wrap
            username (str): The expected username
            password (str): The expected password
            realm (str): The realm shown in the browser's prompt
        """
        self._app = app
        token = base64.b64encode(f"{username}:{password}".encode())
        self._expected = b"Basic " + token
        self._challenge_headers: list[tuple[bytes, bytes]] = [
            (
                b"www-authenticate",
                f'Basic realm="{realm}", charset="UTF-8"'.encode(),
            ),
            (b"content-type", b"text/plain; charset=utf-8"),
        ]

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """
        Gates HTTP requests with the headers set up in `__init__` and passes
        other scopes straight through

        Args:
            scope (Scope): The ASGI connection scope
            receive (Receive): The ASGI receive channel
            send (Send): The ASGI send channel
        """
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        supplied = headers.get(b"authorization")
        if supplied is not None and hmac.compare_digest(
            supplied, self._expected
        ):
            await self._app(scope, receive, send)
            return

        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": self._challenge_headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"Authentication Required",
            }
        )
