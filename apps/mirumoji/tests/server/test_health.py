"""
Smoke test: GET /health/status returns {"status": "ok"}.

This is the minimal test that verifies:
  - The FastAPI app can be instantiated.
  - The DB lifecycle (connect / disconnect) works with SQLite in-memory.
  - The /health/status endpoint responds correctly.
"""

import pytest


@pytest.mark.asyncio
async def test_health_status(client):
    response = await client.get("/health/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
