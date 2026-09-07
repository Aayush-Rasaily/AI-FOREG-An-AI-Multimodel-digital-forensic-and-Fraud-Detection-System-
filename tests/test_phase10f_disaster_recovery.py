"""Tests for Phase 10F backup, DR, and retention."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from backend.app.core.config import Settings
from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD
from backend.app.recovery.backup import BACKUP_ENGINE_VERSION, create_backup_bundle
from backend.app.recovery.restore import plan_restore, validate_restore_bundle
from backend.app.recovery.retention import enforce_retention
from backend.app.recovery.verification import verify_backup_bundle

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def recovery_settings(tmp_path: Path) -> Settings:
    storage = tmp_path / "data"
    (storage / "reports").mkdir(parents=True)
    (storage / "exports").mkdir(parents=True)
    (storage / "reports" / "sample.txt").write_text("report", encoding="utf-8")
    (storage / "exports" / "case.json").write_text("{}", encoding="utf-8")
    return Settings(
        app_env="local",
        storage_root=storage,
        temp_storage_path=storage / "tmp",
        ai_model_root=tmp_path / "models",
        backup_retain_days=30,
        report_retain_days=90,
    )


class TestBackupMetadata:
    def test_create_bundle_records_checksums(
        self,
        recovery_settings: Settings,
    ) -> None:
        manifest = create_backup_bundle(recovery_settings, stamp="TEST20260907T120000Z")
        assert manifest["stamp"] == "TEST20260907T120000Z"
        assert manifest["schema_version"] == EXPECTED_MIGRATION_HEAD
        assert manifest["backup_engine_version"] == BACKUP_ENGINE_VERSION
        assert manifest["manifest_sha256"]
        assert any(item["path"] == "configuration.json" for item in manifest["files"])
        assert any(item["component"] == "reports" for item in manifest["files"])
        bundle = Path(manifest["bundle_dir"])
        assert (bundle / "manifest.json").is_file()


class TestVerificationAndRestore:
    def test_verify_and_validate_restore(
        self,
        recovery_settings: Settings,
    ) -> None:
        manifest = create_backup_bundle(recovery_settings, stamp="TEST20260907T130000Z")
        bundle = Path(manifest["bundle_dir"])
        verified = verify_backup_bundle(bundle)
        assert verified["valid"] is True
        assert verified["status"] in {"PASSED", "PASSED_WITH_WARNINGS"}

        validation = validate_restore_bundle(bundle, recovery_settings)
        assert validation["restore_allowed"] is True
        assert validation["status"] == "READY"

        plan = plan_restore(bundle)
        assert plan["validation"]["restore_allowed"] is True
        assert len(plan["steps"]) >= 5

    def test_tampered_file_fails_verification(
        self,
        recovery_settings: Settings,
    ) -> None:
        manifest = create_backup_bundle(recovery_settings, stamp="TEST20260907T140000Z")
        bundle = Path(manifest["bundle_dir"])
        target = bundle / "configuration.json"
        target.write_text('{"tampered": true}', encoding="utf-8")
        verified = verify_backup_bundle(bundle)
        assert verified["valid"] is False
        assert verified["status"] == "FAILED"
        validation = validate_restore_bundle(bundle, recovery_settings)
        assert validation["restore_allowed"] is False


class TestRetention:
    def test_retention_dry_run_and_apply(
        self,
        recovery_settings: Settings,
        tmp_path: Path,
    ) -> None:
        # Create an expired backup directory with manifest
        old = Path(recovery_settings.storage_root) / "deployment" / "backups" / "old"
        old.mkdir(parents=True)
        (old / "manifest.json").write_text("{}", encoding="utf-8")
        old_mtime = time.time() - (40 * 86400)
        os.utime(old, (old_mtime, old_mtime))

        dry = enforce_retention(recovery_settings, dry_run=True)
        assert dry["dry_run"] is True
        assert any("old" in path for path in dry["removed"])

        applied = enforce_retention(recovery_settings, dry_run=False)
        assert applied["dry_run"] is False
        assert not old.exists()

        # Evidence paths must never be selected for deletion via policy targets
        evidence = Path(recovery_settings.storage_root) / "evidence" / "x"
        evidence.mkdir(parents=True)
        (evidence / "file.bin").write_bytes(b"x")
        result = enforce_retention(recovery_settings, dry_run=False)
        assert evidence.exists()
        assert (evidence / "file.bin").exists()
        assert "policies" in result


class TestArtifacts:
    def test_scripts_and_docs_exist(self) -> None:
        scripts = REPO_ROOT / "deployment" / "scripts"
        for name in (
            "backup.sh",
            "restore.sh",
            "verify_backup.sh",
            "cleanup.sh",
        ):
            assert (scripts / name).is_file()
        assert (REPO_ROOT / "docs" / "disaster-recovery.md").is_file()
        text = (REPO_ROOT / "docs" / "disaster-recovery.md").read_text(
            encoding="utf-8"
        )
        assert "RTO" in text and "RPO" in text
