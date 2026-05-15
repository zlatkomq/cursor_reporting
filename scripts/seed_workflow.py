#!/usr/bin/env python
"""Seed workflow_projects table with sample data."""
from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cursor_metrics.config import get_settings
from cursor_metrics.database import Base
from cursor_metrics.models.db import WorkflowProject

SAMPLE_PROJECTS = [
    # Spec stage
    {"spec_id": "006", "name": "API Rate Limiting", "stage": "spec", "status": "draft", "days_ago": 1},
    {"spec_id": "007", "name": "Email Notifications", "stage": "spec", "status": "in_progress", "days_ago": 3},
    {"spec_id": "008", "name": "Data Export Feature", "stage": "spec", "status": "draft", "days_ago": 0.5},
    # Design stage
    {"spec_id": "004", "name": "User Preferences", "stage": "design", "status": "in_progress", "days_ago": 2},
    {"spec_id": "009", "name": "Audit Logging", "stage": "design", "status": "review", "days_ago": 4},
    {"spec_id": "010", "name": "Webhook Integration", "stage": "design", "status": "in_progress", "days_ago": 1.5},
    # UIX stage
    {"spec_id": "011", "name": "Dashboard Widgets", "stage": "uix", "status": "in_progress", "days_ago": 2},
    {"spec_id": "012", "name": "Settings Redesign", "stage": "uix", "status": "blocked", "days_ago": 5},
    # Tasks stage
    {"spec_id": "003", "name": "Model Pricing Updates", "stage": "tasks", "status": "approved", "days_ago": 1},
    {"spec_id": "013", "name": "Search Feature", "stage": "tasks", "status": "in_progress", "days_ago": 3},
    {"spec_id": "014", "name": "Bulk Operations", "stage": "tasks", "status": "review", "days_ago": 2},
    # Implement stage
    {"spec_id": "002", "name": "Token Analytics", "stage": "implement", "status": "in_progress", "days_ago": 4},
    {"spec_id": "005", "name": "Dashboard Redesign", "stage": "implement", "status": "in_progress", "days_ago": 1},
    {"spec_id": "015", "name": "CI/CD Pipeline", "stage": "implement", "status": "blocked", "days_ago": 6},
    # Review stage
    {"spec_id": "001", "name": "Initial Setup", "stage": "review", "status": "approved", "days_ago": 0.5},
    {"spec_id": "016", "name": "Performance Optimization", "stage": "review", "status": "review", "days_ago": 2},
    {"spec_id": "017", "name": "Security Hardening", "stage": "review", "status": "blocked", "days_ago": 3},
]


async def seed() -> None:
    """Create the workflow_projects table and upsert sample rows."""
    engine = create_async_engine(get_settings().DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(UTC).replace(tzinfo=None)
    inserted = 0
    updated = 0
    skipped = 0

    async with session_factory() as session:
        for row in SAMPLE_PROJECTS:
            entered_at = now - timedelta(days=row["days_ago"])

            result = await session.execute(
                select(WorkflowProject).where(WorkflowProject.spec_id == row["spec_id"])
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                session.add(
                    WorkflowProject(
                        spec_id=row["spec_id"],
                        name=row["name"],
                        stage=row["stage"],
                        status=row["status"],
                        entered_stage_at=entered_at,
                    )
                )
                inserted += 1
            else:
                existing.name = row["name"]
                existing.stage = row["stage"]
                existing.status = row["status"]
                existing.entered_stage_at = entered_at
                existing.updated_at = now
                updated += 1

        await session.commit()

    await engine.dispose()

    total = inserted + updated
    print(f"Seed complete: {total} rows processed ({inserted} inserted, {updated} updated, {skipped} skipped)")
    for row in SAMPLE_PROJECTS:
        print(f"  [{row['stage']:<10}] {row['spec_id']:>3} — {row['name']} ({row['status']})")


if __name__ == "__main__":
    asyncio.run(seed())
