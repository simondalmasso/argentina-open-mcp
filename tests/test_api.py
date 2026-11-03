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
