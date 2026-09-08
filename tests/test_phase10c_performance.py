"""Tests for Phase 10C performance infrastructure."""

from __future__ import annotations

import importlib.util
import time
from pathlib import Path

import pytest
from sqlalchemy import select

from backend.app.ai.bootstrap import build_registry
from backend.app.ai.models.dummy import DummyModel
from backend.app.ai.registry.registry import ModelRegistry
from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD
from backend.app.infrastructure.cache.json_cache import cache_key
from backend.app.infrastructure.concurrency import (
    get_thread_pool,
    run_in_thread,
    shutdown_thread_pool,
)
from backend.app.infrastructure.database.bulk import bulk_add
from backend.app.infrastructure.database.pagination import apply_pagination
from backend.app.models.case import Case
from backend.app.platform_validation.migration_checker import check_migrations
from backend.app.platform_validation.models import CheckStatus

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ROOT / "backend" / "alembic" / "versions"
PERF_MIGRATION = VERSIONS / "20260915_0034_add_performance_indexes.py"


def _load_migration(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMigrationChain:
    def test_performance_migration_present(self) -> None:
        assert PERF_MIGRATION.is_file()
        module = _load_migration(PERF_MIGRATION)
        assert module.revision == "20260915_0034"
        assert module.down_revision == "20260914_0033"
        assert EXPECTED_MIGRATION_HEAD == "20260915_0034"

    def test_platform_validation_migration_checker_passes(self) -> None:
        outcome = check_migrations(repo_root=ROOT / "backend")
        assert outcome.status == CheckStatus.PASS
        assert outcome.details["expected_head"] == "20260915_0034"


class TestConcurrency:
    @pytest.mark.asyncio
    async def test_run_in_thread_executes(self) -> None:
        shutdown_thread_pool(wait=False)
        result = await run_in_thread(lambda x: x + 1, 41)
        assert result == 42
        pool = get_thread_pool()
        assert pool._max_workers >= 1  # noqa: SLF001 — intentional probe
        shutdown_thread_pool(wait=False)


class TestCacheHelpers:
    def test_cache_key_namespaced(self) -> None:
        assert cache_key("ai", "models", "50", "0").startswith("ai_forge:cache:")


class TestPagination:
    def test_apply_pagination_bounds(self) -> None:
        stmt = apply_pagination(select(Case.id), limit=9999, offset=-5)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True})).upper()
        assert "LIMIT 500" in compiled
        assert "OFFSET 0" in compiled


class TestRegistryMetadataCache:
    def test_list_metadata_does_not_reinstantiate(self) -> None:
        created = {"count": 0}

        class CountingModel(DummyModel):
            def __init__(self) -> None:
                created["count"] += 1
                super().__init__()

        registry = ModelRegistry()
        registry.register(CountingModel)
        assert created["count"] == 1
        first = registry.list_metadata()
        second = registry.list_metadata()
        assert first == second
        assert created["count"] == 1
        before = created["count"]
        caps = registry.discover_capabilities()
        assert "dummy" in caps
        assert created["count"] == before

    def test_build_registry_list_is_fast(self) -> None:
        registry = build_registry()
        started = time.perf_counter()
        for _ in range(200):
            _ = registry.list_metadata()
            _ = registry.discover_capabilities()
        elapsed_ms = (time.perf_counter() - started) * 1000
        assert elapsed_ms < 250


class TestBulkHelper:
    @pytest.mark.asyncio
    async def test_bulk_add_empty(self) -> None:
        class _Session:
            def __init__(self) -> None:
                self.added: list[object] = []

            def add_all(self, items: list[object]) -> None:
                self.added.extend(items)

            async def flush(self) -> None:
                return None

        session = _Session()
        assert await bulk_add(session, []) == 0  # type: ignore[arg-type]
        assert session.added == []
