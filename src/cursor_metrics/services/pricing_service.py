"""Model-to-price mapping and cost estimation logic."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select

from cursor_metrics.models.db import ModelPricing

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_TOKENS_PER_EVENT = Decimal(1000)


class PricingService:
    """Maps model identifiers to per-token pricing and computes costs.

    Uses the model_pricing table via its own async session to look up
    cost-per-input-token and cost-per-output-token rates.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_pricing_map(self) -> dict[str, tuple[Decimal, Decimal]]:
        """Return ``{model: (cost_per_input, cost_per_output)}`` from *model_pricing*."""
        result = await self._session.execute(select(ModelPricing))
        rows = result.scalars().all()
        return {
            row.model: (row.cost_per_input_token, row.cost_per_output_token)
            for row in rows
        }

    async def estimate_cost(self, model: str, event_count: int) -> Decimal:
        """Estimate cost for *model* given *event_count*.

        Uses a flat-rate placeholder of ~1 000 tokens per event until real
        token counts are available in the ingest payload.
        """
        pricing_map = await self.get_pricing_map()
        if model not in pricing_map:
            return Decimal(0)
        cost_in, cost_out = pricing_map[model]
        return event_count * (cost_in + cost_out) * _TOKENS_PER_EVENT
