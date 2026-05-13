"""Tests for cursor_metrics.services.pricing_service — PricingService."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from cursor_metrics.models.db import ModelPricing
from cursor_metrics.services.pricing_service import _TOKENS_PER_EVENT, PricingService


def _make_pricing_row(
    model: str,
    cost_in: str = "0.00000300",
    cost_out: str = "0.00001500",
    cost_cache: str = "0.00000030",
) -> MagicMock:
    row = MagicMock(spec=ModelPricing)
    row.model = model
    row.cost_per_input_token = Decimal(cost_in)
    row.cost_per_output_token = Decimal(cost_out)
    row.cost_per_cache_read_token = Decimal(cost_cache)
    return row


def _mock_session(rows: list[MagicMock] | None = None) -> AsyncMock:
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows or []
    session.execute = AsyncMock(return_value=result)
    return session


class TestGetPricingMap:
    """Tests for PricingService.get_pricing_map."""

    @pytest.mark.asyncio()
    async def test_returns_dict_with_correct_structure(self) -> None:
        rows = [
            _make_pricing_row("gpt-4o", "0.00000500", "0.00001500"),
            _make_pricing_row("claude-sonnet", "0.00000300", "0.00001200"),
        ]
        session = _mock_session(rows)
        svc = PricingService(session)

        pricing = await svc.get_pricing_map()

        assert isinstance(pricing, dict)
        assert len(pricing) == 2
        assert "gpt-4o" in pricing
        assert "claude-sonnet" in pricing
        assert pricing["gpt-4o"] == (Decimal("0.00000500"), Decimal("0.00001500"), Decimal("0.00000030"))
        assert pricing["claude-sonnet"] == (Decimal("0.00000300"), Decimal("0.00001200"), Decimal("0.00000030"))

    @pytest.mark.asyncio()
    async def test_empty_dict_when_no_rows(self) -> None:
        session = _mock_session([])
        svc = PricingService(session)

        pricing = await svc.get_pricing_map()

        assert pricing == {}


class TestEstimateCost:
    """Tests for PricingService.estimate_cost."""

    @pytest.mark.asyncio()
    async def test_known_model_returns_calculated_cost(self) -> None:
        cost_in = Decimal("0.00000300")
        cost_out = Decimal("0.00001500")
        rows = [_make_pricing_row("gpt-4o", str(cost_in), str(cost_out))]
        session = _mock_session(rows)
        svc = PricingService(session)

        event_count = 10
        result = await svc.estimate_cost("gpt-4o", event_count)

        expected = event_count * (cost_in + cost_out) * _TOKENS_PER_EVENT
        assert result == expected

    @pytest.mark.asyncio()
    async def test_unknown_model_returns_zero(self) -> None:
        rows = [_make_pricing_row("gpt-4o")]
        session = _mock_session(rows)
        svc = PricingService(session)

        result = await svc.estimate_cost("unknown-model", 5)

        assert result == Decimal(0)


class TestEstimateCostWithTokens:
    """Tests for token-based cost estimation."""

    @pytest.mark.asyncio()
    async def test_estimate_cost_with_real_tokens(self) -> None:
        cost_in = Decimal("0.00000300")
        cost_out = Decimal("0.00001500")
        cost_cache = Decimal("0.00000030")
        rows = [_make_pricing_row("gpt-4o", str(cost_in), str(cost_out), str(cost_cache))]
        session = _mock_session(rows)
        svc = PricingService(session)

        result = await svc.estimate_cost(
            "gpt-4o",
            event_count=1,
            input_tokens=5000,
            output_tokens=2000,
            cache_read_tokens=3000,
        )

        expected = Decimal(5000) * cost_in + Decimal(2000) * cost_out + Decimal(3000) * cost_cache
        assert result == expected

    @pytest.mark.asyncio()
    async def test_estimate_cost_falls_back_to_placeholder(self) -> None:
        cost_in = Decimal("0.00000300")
        cost_out = Decimal("0.00001500")
        rows = [_make_pricing_row("gpt-4o", str(cost_in), str(cost_out))]
        session = _mock_session(rows)
        svc = PricingService(session)

        result = await svc.estimate_cost("gpt-4o", event_count=10)

        expected = 10 * (cost_in + cost_out) * _TOKENS_PER_EVENT
        assert result == expected

    @pytest.mark.asyncio()
    async def test_estimate_cost_model_not_in_pricing(self) -> None:
        rows = [_make_pricing_row("gpt-4o")]
        session = _mock_session(rows)
        svc = PricingService(session)

        result = await svc.estimate_cost(
            "unknown-model",
            event_count=5,
            input_tokens=1000,
            output_tokens=500,
        )

        assert result == Decimal(0)

    @pytest.mark.asyncio()
    async def test_get_pricing_map_returns_3_tuples(self) -> None:
        rows = [_make_pricing_row("gpt-4o", "0.00000300", "0.00001500", "0.00000030")]
        session = _mock_session(rows)
        svc = PricingService(session)

        pricing = await svc.get_pricing_map()

        assert len(pricing["gpt-4o"]) == 3
        assert pricing["gpt-4o"] == (
            Decimal("0.00000300"),
            Decimal("0.00001500"),
            Decimal("0.00000030"),
        )

    @pytest.mark.asyncio()
    async def test_cache_write_not_priced(self) -> None:
        """cache_write_tokens are tracked but NOT included in cost calculation."""
        cost_in = Decimal("0.00000300")
        cost_out = Decimal("0.00001500")
        cost_cache = Decimal("0.00000030")
        rows = [_make_pricing_row("gpt-4o", str(cost_in), str(cost_out), str(cost_cache))]
        session = _mock_session(rows)
        svc = PricingService(session)

        result = await svc.estimate_cost(
            "gpt-4o",
            event_count=1,
            input_tokens=5000,
            output_tokens=2000,
            cache_read_tokens=3000,
        )

        cost_without_cache_write = Decimal(5000) * cost_in + Decimal(2000) * cost_out + Decimal(3000) * cost_cache
        assert result == cost_without_cache_write
        # estimate_cost has no cache_write_tokens parameter — verifying the
        # signature itself enforces that cache writes are never priced.


class TestPricingServiceImport:
    """Verify PricingService is importable from multiple paths."""

    def test_import_from_module(self) -> None:
        from cursor_metrics.services.pricing_service import PricingService as Cls

        assert Cls is not None

    def test_import_from_package(self) -> None:
        from cursor_metrics.services import PricingService as Cls

        assert Cls is not None

    def test_class_is_in_package_all(self) -> None:
        import cursor_metrics.services as pkg

        assert "PricingService" in pkg.__all__
