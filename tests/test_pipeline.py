from datetime import UTC, datetime

from argentina_open_data.pipeline import capture_georef_snapshot
from argentina_open_data.snapshots import SnapshotStore
from argentina_open_data.sources.georef import GeorefPage, GeorefRecord, GeorefResource


class FakeGeoref:
    BASE_URL = "https://apis.datos.gob.ar/georef/api/v2.0"
    ATTRIBUTION = "Servicio Georef"

    def __init__(self):
        self.calls = []

    def list(self, resource, *, limit, offset, province_id=None):
        self.calls.append((resource, limit, offset))
        if offset == 0:
            records = (
                GeorefRecord("82", "Santa Fe", resource, {"id": "82", "nombre": "Santa Fe"}),
            )
            return GeorefPage(records, 1, 2, 0, resource)
        return GeorefPage(
            (GeorefRecord("06", "Buenos Aires", resource, {"id": "06", "nombre": "Buenos Aires"}),),
            1,
            2,
            1,
            resource,
        )


def test_pipeline_is_bounded_and_saves_snapshot(tmp_path):
    client = FakeGeoref()
    digest, total = capture_georef_snapshot(
        GeorefResource.PROVINCES,
        store=SnapshotStore(tmp_path),
        client=client,
        limit=1,
        max_pages=1,
    )
    manifests = SnapshotStore(tmp_path).list_manifests()
    assert digest == manifests[0].snapshot_sha256
    assert total == 2
    assert len(client.calls) == 1
    assert manifests[0].record_count == 1


def test_pipeline_explicitly_allows_more_pages(tmp_path):
    client = FakeGeoref()
    capture_georef_snapshot(
        GeorefResource.PROVINCES,
        store=SnapshotStore(tmp_path),
        client=client,
        limit=1,
        max_pages=2,
    )
    assert len(client.calls) == 2
