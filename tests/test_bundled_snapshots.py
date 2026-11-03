from argentina_open_data.bundled_snapshots import BundledSnapshotStore
from argentina_open_data.contracts import GeoLevel
from argentina_open_data.snapshots import SnapshotError


def test_bundled_snapshot_store_exposes_verified_provinces():
    store = BundledSnapshotStore()
    manifests = store.list_manifests("georef.territories")

    assert len(manifests) == 1
    manifest = manifests[0]
    assert manifest.resource == "provincias"
    assert manifest.snapshot_sha256 == (
        "4d8edd0461a34878ccd72e7ccde17fc523c22946867e5e4e073886c3811abbdb"
    )
    assert manifest.record_count == 24

    document = store.load(manifest)
    santa_fe = next(
        item.territory
        for item in document.records
        if item.territory.geo_id == "82"
    )
    assert santa_fe.name == "Santa Fe"
    assert santa_fe.level == GeoLevel.PROVINCE


def test_bundled_snapshot_store_rejects_path_escape():
    store = BundledSnapshotStore()
    manifest = store.list_manifests()[0].model_copy(
        update={"document_path": "../outside.json"}
    )

    try:
        store.load(manifest)
    except SnapshotError as exc:
        assert "escapes" in str(exc)
    else:
        raise AssertionError("path traversal must be rejected")
