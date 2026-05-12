"""Model-to-price mapping and cost estimation logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PricingService:
    """Maps model identifiers to per-token pricing and computes costs.

    Uses the model_pricing table via its own async session to look up
    cost-per-input-token and cost-per-output-token rates.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
