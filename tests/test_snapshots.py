from datetime import UTC, datetime

import pytest

from argentina_open_data.contracts import GeoLevel, Territory
from argentina_open_data.snapshots import (
    SnapshotDocument,
    SnapshotError,
    SnapshotRecord,
    SnapshotStore,
)


def document() -> SnapshotDocument:
    return SnapshotDocument(
        source_id="georef.territories",
        resource="provincias",
        source_url="https://apis.datos.gob.ar/georef/api/v2.0/provincias",
        license_id="CC-BY-4.0",
        attribution="Servicio Georef",
        retrieved_at=datetime(2026, 11, 3, tzinfo=UTC),
        records=(
            SnapshotRecord(
                territory=Territory(
                    geo_id="82",
                    name="Santa Fe",
                    level=GeoLevel.PROVINCE,
                    source_system="georef-v2",
                ),
                source_record={"id": "82", "nombre": "Santa Fe"},
            ),
        ),
    )


def test_snapshot_is_content_addressed_and_immutable(tmp_path):
    store = SnapshotStore(tmp_path)
    first = store.save(document())
    second = store.save(document())
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert len(store.list_manifests()) == 1
    assert store.load(first).records[0].territory.name == "Santa Fe"


def test_snapshot_hash_tampering_is_detected(tmp_path):
    store = SnapshotStore(tmp_path)
    manifest = store.save(document())
    path = tmp_path / manifest.document_path
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(SnapshotError, match="hash verification"):
        store.load(manifest)


def test_snapshot_rejects_path_escape(tmp_path):
    store = SnapshotStore(tmp_path)
    manifest = store.save(document()).model_copy(update={"document_path": "../outside.json"})
    with pytest.raises(SnapshotError, match="escapes"):
        store.load(manifest)


def test_snapshots_are_empty_before_first_ingestion(tmp_path):
    assert SnapshotStore(tmp_path).list_manifests() == ()
