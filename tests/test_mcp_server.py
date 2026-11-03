import asyncio

from argentina_open_data import mcp_server


def test_mcp_source_tool_returns_registry():
    result = asyncio.run(mcp_server.list_data_sources())
    assert {item["source_id"] for item in result["sources"]} >= {
        "georef.territories",
        "bcra.website-content",
        "indec.api-catalog",
    }


def test_mcp_search_does_not_invent_missing_snapshots(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp_server, "store", mcp_server.SnapshotStore(tmp_path))
    result = asyncio.run(mcp_server.search_territories())
    assert result["error"] == "dataset_not_ingested"


def test_mcp_search_validates_resource_and_limit():
    assert asyncio.run(mcp_server.search_territories(resource="unknown"))["error"] == "unsupported_resource"
    assert asyncio.run(mcp_server.search_territories(limit=1000))["error"] == "limit_must_be_between_1_and_100"


def test_mcp_search_returns_snapshot_and_provenance(monkeypatch, tmp_path):
    from datetime import UTC, datetime

    from argentina_open_data.contracts import GeoLevel, Territory
    from argentina_open_data.snapshots import SnapshotDocument, SnapshotRecord

    store = mcp_server.SnapshotStore(tmp_path)
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
    monkeypatch.setattr(mcp_server, "store", store)
    result = asyncio.run(mcp_server.search_territories(query="santa"))
    assert result["data"][0]["geo_id"] == "82"
    assert result["meta"]["license_id"] == "CC-BY-4.0"
