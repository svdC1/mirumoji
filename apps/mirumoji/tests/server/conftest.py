"""
Shared pytest fixtures for server tests

Provides:
- `client`: an httpx `AsyncClient` wired to the FastAPI app

"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from mirumoji.server.app import create_app

# Provide placeholder env vars so capability detection has deterministic
# values during collection (no real provider/Modal calls are made).
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("MODAL_TOKEN_ID", "test-modal-id")
os.environ.setdefault("MODAL_TOKEN_SECRET", "test-modal-secret")


@pytest.fixture
async def client():
    """AsyncClient pointed at the FastAPI app (no lifespan)"""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
