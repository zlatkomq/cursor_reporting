"""CLI tool for cursor-metrics administration."""

from __future__ import annotations

import argparse
import asyncio
import sys
from decimal import Decimal

# Model pricing: (cost_per_input_token, cost_per_output_token, cost_per_cache_read_token)
# Rates in USD per token. Source: provider pricing pages as of 2026-05.
DEFAULT_PRICING: dict[str, tuple[Decimal, Decimal, Decimal]] = {
    # Anthropic Claude
    "claude-opus-4-6": (Decimal("0.00001500"), Decimal("0.00007500"), Decimal("0.00000150")),
    "claude-opus-4-5": (Decimal("0.00001500"), Decimal("0.00007500"), Decimal("0.00000150")),
    "claude-sonnet-4-5": (Decimal("0.00000300"), Decimal("0.00001500"), Decimal("0.00000030")),
    "claude-sonnet-4": (Decimal("0.00000300"), Decimal("0.00001500"), Decimal("0.00000030")),
    "claude-4.6-sonnet-medium-thinking": (Decimal("0.00000300"), Decimal("0.00001500"), Decimal("0.00000030")),
    "claude-4.6-opus-high-thinking": (Decimal("0.00001500"), Decimal("0.00007500"), Decimal("0.00000150")),
    "claude-opus-4-7-thinking-xhigh": (Decimal("0.00001500"), Decimal("0.00007500"), Decimal("0.00000150")),
    # OpenAI
    "gpt-4o": (Decimal("0.00000250"), Decimal("0.00001000"), Decimal("0.00000125")),
    "gpt-4o-mini": (Decimal("0.00000015"), Decimal("0.00000060"), Decimal("0.00000008")),
    "gpt-4.1": (Decimal("0.00000200"), Decimal("0.00000800"), Decimal("0.00000050")),
    "gpt-4.1-mini": (Decimal("0.00000040"), Decimal("0.00000160"), Decimal("0.00000010")),
    "gpt-4.1-nano": (Decimal("0.00000010"), Decimal("0.00000040"), Decimal("0.00000003")),
    "o3": (Decimal("0.00001000"), Decimal("0.00004000"), Decimal("0.00000250")),
    "o3-mini": (Decimal("0.00000110"), Decimal("0.00000440"), Decimal("0.00000055")),
    "o4-mini": (Decimal("0.00000110"), Decimal("0.00000440"), Decimal("0.00000055")),
    "gpt-5.3-codex": (Decimal("0.00000250"), Decimal("0.00001000"), Decimal("0.00000125")),
    "gpt-5.5-medium": (Decimal("0.00000200"), Decimal("0.00000800"), Decimal("0.00000050")),
    # Cursor built-in
    "cursor-small": (Decimal("0.00000010"), Decimal("0.00000010"), Decimal("0.00000001")),
}


async def create_user(email: str, password: str) -> None:
    """Create a dashboard user with hashed password."""
    from sqlalchemy.exc import IntegrityError

    from cursor_metrics.database import AsyncSessionLocal
    from cursor_metrics.repositories.user_repo import UserRepository
    from cursor_metrics.services.auth_service import AuthService

    password_hash = AuthService.hash_password(password)
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        try:
            await repo.create(email=email, password_hash=password_hash)
            await session.commit()
        except IntegrityError:
            print(f"Error: user with email '{email}' already exists.", file=sys.stderr)
            sys.exit(1)
    print(f"Created user: {email}")


async def seed_pricing() -> None:
    """Insert or update model pricing from the built-in defaults."""
    from sqlalchemy import select

    from cursor_metrics.database import AsyncSessionLocal
    from cursor_metrics.models.db import ModelPricing

    async with AsyncSessionLocal() as session:
        inserted = 0
        updated = 0
        for model, (cost_in, cost_out, cost_cache) in DEFAULT_PRICING.items():
            result = await session.execute(select(ModelPricing).where(ModelPricing.model == model))
            existing = result.scalar_one_or_none()
            if existing:
                existing.cost_per_input_token = cost_in
                existing.cost_per_output_token = cost_out
                existing.cost_per_cache_read_token = cost_cache
                updated += 1
            else:
                session.add(
                    ModelPricing(
                        model=model,
                        cost_per_input_token=cost_in,
                        cost_per_output_token=cost_out,
                        cost_per_cache_read_token=cost_cache,
                    )
                )
                inserted += 1
        await session.commit()
    print(f"Model pricing seeded: {inserted} inserted, {updated} updated ({len(DEFAULT_PRICING)} total models)")


def main() -> None:
    """Entry point for the cursor-metrics CLI."""
    parser = argparse.ArgumentParser(description="Cursor Metrics CLI")
    subparsers = parser.add_subparsers(dest="command")

    create_cmd = subparsers.add_parser("create-user", help="Create a dashboard user")
    create_cmd.add_argument("--email", required=True, help="User email")
    create_cmd.add_argument("--password", required=True, help="User password")

    subparsers.add_parser("seed-pricing", help="Seed model_pricing with default token rates")

    args = parser.parse_args()

    if args.command == "create-user":
        asyncio.run(create_user(args.email, args.password))
    elif args.command == "seed-pricing":
        asyncio.run(seed_pricing())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
