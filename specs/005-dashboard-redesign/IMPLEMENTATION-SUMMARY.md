## Implementation Summary

### T1: Add WorkflowProject ORM model
**Files:** created: [tests/test_workflow_model.py], modified: [src/cursor_metrics/models/db.py, src/cursor_metrics/models/__init__.py]
**Patterns:** Followed existing MetricsEvent/ModelPricing/DashboardUser ORM pattern — Integer PK, mapped_column, Mapped types, Index in __table_args__
**Decisions:** Used Integer (not BigInteger) for id PK matching existing models; no Python-level enum for stage/status — belongs in service layer
**Deviations:** None
**Implementer:** 41bfa907-2798-4ab3-aee2-081ee9191de2 [2026-05-15 11:03]
**Review:** Skipped per velocity — controller-verified (17 tests pass, lint clean, no regressions)
