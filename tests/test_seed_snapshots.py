import json
from datetime import UTC, datetime
from pathlib import Path

from argentina_open_data.contracts import GeoLevel, Territory
from argentina_open_data.seed_snapshots import seed_snapshot_documents
from argentina_open_data.snapshots import SnapshotDocument, SnapshotRecord, SnapshotStore


def snapshot_document() -> SnapshotDocument:
    return SnapshotDocument(
        source_id="georef.territories",
        resource="provincias",
        source_url="https://apis.datos.gob.ar/georef/api/v2.0/provincias",
        license_id="CC-BY-4.0",
        attribution="Servicio Georef – https://www.argentina.gob.ar/georef",
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


def test_seed_import_is_idempotent(tmp_path):
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    document = snapshot_document()
    (seed_dir / "provincias.json").write_text(
        json.dumps(document.model_dump(mode="json"), ensure_ascii=False),
        encoding="utf-8",
    )
    store = SnapshotStore(tmp_path / "volume")

    assert seed_snapshot_documents(seed_dir, store) == 1
    first = store.list_manifests()
    assert len(first) == 1
    assert first[0].record_count == 1
    assert store.load(first[0]).records[0].territory.geo_id == "82"

    assert seed_snapshot_documents(seed_dir, store) == 1
    second = store.list_manifests()
    assert len(second) == 1
    assert second[0].snapshot_sha256 == first[0].snapshot_sha256


def test_seed_import_with_missing_directory_is_empty(tmp_path):
    store = SnapshotStore(tmp_path / "volume")
    assert seed_snapshot_documents(tmp_path / "missing", store) == 0
    assert store.list_manifests() == ()


def test_bundled_georef_provinces_snapshot_has_expected_coverage_and_hash(tmp_path):
    seed_dir = Path(__file__).parents[1] / "data" / "seed-snapshots"
    store = SnapshotStore(tmp_path / "volume")

    assert seed_snapshot_documents(seed_dir, store) == 1
    manifests = store.list_manifests("georef.territories")
    assert len(manifests) == 1
    manifest = manifests[0]
    assert manifest.snapshot_sha256 == (
        "4d8edd0461a34878ccd72e7ccde17fc523c22946867e5e4e073886c3811abbdb"
    )
    assert manifest.record_count == 24

    document = store.load(manifest)
    santa_fe = next(record.territory for record in document.records if record.territory.geo_id == "82")
    assert santa_fe.name == "Santa Fe"
    assert santa_fe.level == GeoLevel.PROVINCE
