from fastapi.testclient import TestClient

from argentina_open_data import api


def test_health_and_catalog_endpoints():
    client = TestClient(api.app)
    assert client.get("/health").json()["status"] == "ok"
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    assert response.json()["count"] >= 2


def test_territories_are_not_fabricated_before_ingestion(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "store", api.SnapshotStore(tmp_path))
    response = TestClient(api.app).get("/api/v1/territories")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "dataset_not_ingested"


def test_homepage_is_served():
    response = TestClient(api.app).get("/")
    assert response.status_code == 200
    assert "Argentina Open Data" in response.text



def test_territories_returns_snapshot_provenance(monkeypatch, tmp_path):
    from datetime import UTC, datetime

    from argentina_open_data.contracts import GeoLevel, Territory
    from argentina_open_data.snapshots import SnapshotDocument, SnapshotRecord

    store = api.SnapshotStore(tmp_path)
    store.save(
        SnapshotDocument(
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
    )
    monkeypatch.setattr(api, "store", store)
    response = TestClient(api.app).get("/api/v1/territories?q=santa")
    assert response.status_code == 200
    body = response.json()
    assert body["data"][0]["name"] == "Santa Fe"
    assert body["meta"]["snapshot"]["license_id"] == "CC-BY-4.0"
