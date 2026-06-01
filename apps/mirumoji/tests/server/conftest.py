"""
Shared pytest fixtures for server tests.

Provides:
- ``client``: an httpx AsyncClient wired to the FastAPI app with an in-memory
  SQLite database (DATABASE_URL overridden via env var before the app module
  is imported).
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Set required env vars BEFORE any app module is imported.
# Use plain sqlite:// so SQLAlchemy's sync create_engine (used for
# METADATA.create_all at import time) and the `databases` async client
# both work against the same in-memory database.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
# Routers instantiate Processor() at module level (DI cleanup is 3.x work).
# Provide dummy values so check_env() doesn't raise during collection.
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("MODAL_TOKEN_ID", "test-modal-id")
os.environ.setdefault("MODAL_TOKEN_SECRET", "test-modal-secret")

# Processor() is instantiated at module level in each router (DI antipattern,
# fixed in 3.x). Its __init__ calls fugashi.Tagger() which requires the unidic
# dictionary to be downloaded — not available in CI or local dev without a
# manual `python -m unidic download`. Patch the whole class before importing
# the app so the module-level `processor = Processor()` gets a MagicMock
# instead and MeCab is never touched.
with patch("mirumoji.server.processing.Processor.Processor", MagicMock()):
    from mirumoji.server.db.db import connect_db, disconnect_db

    from mirumoji.server.app import app


@pytest.fixture(scope="session")
async def client():
    """AsyncClient pointed at the FastAPI app with an in-memory database."""
    await connect_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await disconnect_db()
