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
import hashlib
import hmac
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

# Define The ASGI Types To Avoid Importing Starlette
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_COOKIE_NAME = "mirumoji_auth"
"""
Name of the cookie that persists a passed `HTTP Basic Auth` check
"""

_COOKIE_MAX_AGE = 60 * 60 * 24 * 30
"""
Lifetime in seconds of the persistent auth cookie (30 days)

info: Why A Cookie
    - An installed `iOS` `PWA` does not retain the browser's `Basic Auth`
      credential cache across suspend or close, so it re-prompts for the
      password on every reopen

    - After a passed `Basic Auth` check, the middleware sets this cookie and
      then accepts it in place of the credentials, so a reopened `PWA`
      authenticates silently until the cookie expires
"""

_PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/manifest.webmanifest",
        "/favicon.ico",
        "/icons/icon-192.png",
        "/icons/icon-512.png",
        "/screenshots/desktop_screenshot.png",
        "/screenshots/mobile_screenshot.png",
    }
)
"""
The exact request paths served without auth so that the PWA can install behind
the gate

info: Source Of Truth
    - files under `apps/frontend/public/` + the icons and screenshots declared
      in the vite PWA manifest

    - Every entry is a real, unhashed file, so an ungated request can never
      fall through to the SPA shell
"""


def _is_public_asset(path: str) -> bool:
    """
    Reports whether a request path is a public `PWA` install asset served
    without `HTTP Basic Auth`

    question: Why Ungate These
        - The browser fetches the web app manifest, its icons, and the
          `apple-touch-icon` as install-prompt subresources, and `iOS Safari`
          does not attach the cached Basic Auth credentials to them

        - If left gated, they answer `401`, so the install prompt has no name
          or icon and the home-screen icon never renders

        - They carry no user data, so serving exactly these files open keeps
          the shell, the hashed assets, and the API fully gated while letting
          the `PWA` install

    info: Exact Match Only
        Only the real files are ungated (no prefix), so an ungated path always
        resolves to a genuine file and can never reach the `SPA` catch-all,
        which would otherwise serve the gated `index.html` to an
        unauthenticated client

    Args:
        path (str): The request path from the ASGI scope

    Returns:
        `True` when the path is a public install asset
    """
    return path in _PUBLIC_PATHS


class BasicAuthMiddleware:
    """
    Pure-ASGI middleware that gates every request behind `HTTP Basic Auth`

    info: Browser-Native
        - A `401` with a `WWW-Authenticate: Basic` header makes the browser
          show its own credential prompt and then send `Authorization: Basic`
          on every later request, including the top-level navigation

        - This needs no login page or session, so the server and the frontend
          are unchanged

    info: Constant-Time
        The credentials and the cookie are compared with `hmac.compare_digest`,
        so the check does not leak the secret through timing

    info: Public Install Assets
        A short allowlist of `PWA` install files (the manifest, icons, and
        screenshots) is served without auth, since the browser fetches them
        without credentials and gating them breaks the install (see
        `_is_public_asset`)

    info: Persistent Cookie
        - After a passed check, the middleware sets a signed cookie derived
          from the password and accepts that cookie in place of the credentials

        - An installed `iOS` `PWA` drops the browser's `Basic Auth` cache when
          it is suspended or closed, so without the cookie it re-prompts on
          every reopen. The cookie persists that state, and rotating the
          password invalidates every previously issued cookie
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
        # A stateless token derived from the password, so the cookie is
        # validated without any server-side session store. Rotating the
        # password changes this token and invalidates every previously
        # issued cookie
        self._cookie_token = hmac.new(
            password.encode(), b"mirumoji-auth", hashlib.sha256
        ).hexdigest()
        cookie = (
            f"{_COOKIE_NAME}={self._cookie_token}; "
            f"Max-Age={_COOKIE_MAX_AGE}; "
            "Path=/; Secure; HttpOnly; SameSite=Lax"
        )
        self._set_cookie_header = (b"set-cookie", cookie.encode("latin-1"))
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
        Gates HTTP requests, letting a valid persistent cookie or `Basic Auth`
        through and passing other scopes and the public `PWA` install assets
        straight through

        Args:
            scope (Scope): The ASGI connection scope
            receive (Receive): The ASGI receive channel
            send (Send): The ASGI send channel
        """
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        if _is_public_asset(scope.get("path", "")):
            await self._app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])

        # A valid persistent cookie authenticates silently, so an installed PWA
        # that dropped its Basic Auth cache on suspend is not re-prompted
        if self._cookie_valid(headers.get(b"cookie")):
            await self._app(scope, receive, send)
            return

        # A valid Basic Auth check passes and mints the cookie for next time
        supplied = headers.get(b"authorization")
        if supplied is not None and hmac.compare_digest(
            supplied, self._expected
        ):
            await self._app(scope, receive, self._send_with_cookie(send))
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

    def _cookie_valid(self, cookie_header: bytes | None) -> bool:
        """
        Reports whether the request carries a valid persistent auth cookie

        Args:
            cookie_header (bytes | None): The raw `Cookie` request header, or
                `None` when absent

        Returns:
            `True` when the cookie's value matches the expected token
        """
        if not cookie_header:
            return False
        for part in cookie_header.decode("latin-1").split(";"):
            name, _, value = part.strip().partition("=")
            if name == _COOKIE_NAME:
                return hmac.compare_digest(value, self._cookie_token)
        return False

    def _send_with_cookie(self, send: Send) -> Send:
        """
        Wraps `send` so the persistent auth cookie is set on the response

        Injects the `Set-Cookie` header into the response start, so a client
        that just passed `Basic Auth` carries the cookie on its next visit

        Args:
            send (Send): The ASGI send channel to wrap

        Returns:
            A send channel that adds the cookie to the response start
        """

        async def wrapped(message: Message) -> None:
            if message["type"] == "http.response.start":
                cookied = list(message.get("headers") or [])
                cookied.append(self._set_cookie_header)
                message = {**message, "headers": cookied}
            await send(message)

        return wrapped
