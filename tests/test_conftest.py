"""Tests to verify shared conftest fixtures work correctly."""

from __future__ import annotations

from httpx import AsyncClient


class TestAsyncClientFixture:
    """Verify the async_client fixture produces a usable client."""

    async def test_async_client_is_instance(self, async_client: AsyncClient) -> None:
        assert isinstance(async_client, AsyncClient)

    async def test_async_client_can_reach_health(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_async_client_base_url(self, async_client: AsyncClient) -> None:
        assert str(async_client.base_url) == "http://test"
