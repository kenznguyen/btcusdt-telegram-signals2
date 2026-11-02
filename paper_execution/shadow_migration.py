"""P5.2.4 RED-only API stub.

This deliberately performs no migration or verification. It exists only so the
contract suite can import the public API and execute all test methods. Calls are
restricted to the disposable unittest fixture directory.
"""
import json
import sqlite3
from pathlib import Path


class ShadowMigrationNotImplemented(RuntimeError):
    """Raised only when the RED stub is used outside its test fixture."""


def _fixture_paths(source_db, t0_target_db, paper_target_db, manifest_dir, migration_id):
    source = Path(source_db).resolve()
    t0 = Path(t0_target_db).resolve()
    paper = Path(paper_target_db).resolve()
    manifests = Path(manifest_dir).resolve()
    root = source.parent.parent
    if (
        not root.name.startswith("p5_2_4_shadow_")
        or t0.parent.parent != root
        or paper.parent.parent != root
        or migration_id != "p5-2-4-fixture-migration-001"
    ):
        raise ShadowMigrationNotImplemented(
            "RED stub is restricted to disposable P5.2.4 unittest fixtures"
        )
    return source, t0, paper, manifests


def migrate_shadow(*, source_db, t0_target_db, paper_target_db,
                   manifest_dir, migration_id, paper_config, **options):
    """Create empty disposable targets and placeholder manifests; copy nothing."""
    source, t0, paper, manifests = _fixture_paths(
        source_db, t0_target_db, paper_target_db, manifest_dir, migration_id
    )
    t0.parent.mkdir(parents=True, exist_ok=True)
    paper.parent.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    for target in (t0, paper):
        with sqlite3.connect(target):
            pass
    (manifests / "source_manifest.json").write_text(json.dumps({
        "tables": [],
        "integrity_check": "NOT_IMPLEMENTED",
        "database_sha256": "",
    }, sort_keys=True))
    (manifests / "migration_manifest.json").write_text(json.dumps({
        "migration_id": migration_id,
        "paper_config": {},
        "paper_config_sha256": "",
        "paper_row_fingerprints": {"source": {}, "target": {}},
        "t0_candle_fingerprint": {"source": "", "target": ""},
    }, sort_keys=True))
    return {"status": "NOT_IMPLEMENTED", "migration_id": migration_id}


def verify_shadow_migration(*, source_db, t0_target_db, paper_target_db,
                            manifest_dir, migration_id, paper_config, **options):
    """Return an explicit non-verdict; fail-closed verification is not implemented."""
    _fixture_paths(source_db, t0_target_db, paper_target_db, manifest_dir, migration_id)
    return {"status": "NOT_IMPLEMENTED", "migration_id": migration_id}
