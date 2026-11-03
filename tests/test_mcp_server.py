from argentina_open_data import mcp_server


def test_mcp_source_tool_returns_registry():
    result = mcp_server.list_data_sources()
    assert {item["source_id"] for item in result["sources"]} >= {
        "georef.territories",
        "bcra.website-content",
    }


def test_mcp_search_does_not_invent_missing_snapshots(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp_server, "store", mcp_server.SnapshotStore(tmp_path))
    result = mcp_server.search_territories()
    assert result["error"] == "dataset_not_ingested"


def test_mcp_search_validates_resource_and_limit():
    assert mcp_server.search_territories(resource="unknown")["error"] == "unsupported_resource"
    assert mcp_server.search_territories(limit=1000)["error"] == "limit_must_be_between_1_and_100"
