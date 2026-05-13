"""CLI tool for cursor-metrics administration."""

from __future__ import annotations

import argparse
import asyncio
import sys


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


def main() -> None:
    """Entry point for the cursor-metrics CLI."""
    parser = argparse.ArgumentParser(description="Cursor Metrics CLI")
    subparsers = parser.add_subparsers(dest="command")

    create_cmd = subparsers.add_parser("create-user", help="Create a dashboard user")
    create_cmd.add_argument("--email", required=True, help="User email")
    create_cmd.add_argument("--password", required=True, help="User password")

    args = parser.parse_args()

    if args.command == "create-user":
        asyncio.run(create_user(args.email, args.password))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
