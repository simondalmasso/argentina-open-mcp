import json
from urllib.parse import parse_qs, urlparse

import pytest

from argentina_open_data.contracts import GeoLevel
from argentina_open_data.sources.georef import GeorefClient, GeorefError, GeorefResource


class FakeResponse:
    status = 200
    headers = {"Content-Length": "160"}

    def __init__(self, payload):
        self.body = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        return self.body if size < 0 else self.body[:size]


def test_georef_client_parses_province_page_and_keeps_official_id(monkeypatch):
    payload = {
        "provincias": [
            {
                "id": "82",
                "nombre": "Santa Fe",
                "centroide": {"lat": -30.7, "lon": -60.5},
            }
        ],
        "cantidad": 1,
        "total": 24,
        "inicio": 0,
        "parametros": {},
    }
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        return FakeResponse(payload)

    monkeypatch.setattr("argentina_open_data.sources.georef.urlopen", fake_urlopen)
    page = GeorefClient(min_request_interval_seconds=0).list(
        GeorefResource.PROVINCES, limit=50, offset=0
    )

    assert page.total == 24
    assert page.records[0].id == "82"
    assert page.records[0].name == "Santa Fe"
    territory = page.records[0].to_territory()
    assert territory.geo_id == "82"
    assert territory.level == GeoLevel.PROVINCE
    assert territory.source_system == "georef-v2"
    query = parse_qs(urlparse(seen["url"]).query)
    assert query["max"] == ["50"]
    assert seen["timeout"] > 0


def test_department_query_is_scoped_to_official_province_code(monkeypatch):
    payload = {
        "departamentos": [
            {"id": "82084", "nombre": "Rosario", "provincia": {"id": "82", "nombre": "Santa Fe"}}
        ],
        "cantidad": 1,
        "total": 19,
        "inicio": 0,
        "parametros": {},
    }
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return FakeResponse(payload)

    monkeypatch.setattr("argentina_open_data.sources.georef.urlopen", fake_urlopen)
    page = GeorefClient(min_request_interval_seconds=0).list(
        GeorefResource.DEPARTMENTS, province_id="82"
    )
    territory = page.records[0].to_territory()

    assert territory.geo_id == "82084"
    assert territory.parent_geo_id == "82"
    assert territory.level == GeoLevel.DEPARTMENT
    assert parse_qs(urlparse(seen["url"]).query)["provincia"] == ["82"]


def test_georef_client_rejects_invalid_limits_and_unknown_resources():
    client = GeorefClient(min_request_interval_seconds=0)
    with pytest.raises(ValueError):
        client.list(GeorefResource.PROVINCES, limit=0)
    with pytest.raises(ValueError):
        client.list(GeorefResource.PROVINCES, limit=1001)


def test_georef_client_rejects_malformed_payload(monkeypatch):
    monkeypatch.setattr(
        "argentina_open_data.sources.georef.urlopen",
        lambda *_args, **_kwargs: FakeResponse({"unexpected": []}),
    )
    with pytest.raises(GeorefError, match="missing expected result collection"):
        GeorefClient(min_request_interval_seconds=0).list(GeorefResource.PROVINCES)


def test_georef_client_enforces_response_size_limit(monkeypatch):
    class OversizedResponse(FakeResponse):
        def read(self, size=-1):
            return b"x" * (size + 1)

    monkeypatch.setattr(
        "argentina_open_data.sources.georef.urlopen",
        lambda *_args, **_kwargs: OversizedResponse({}),
    )
    with pytest.raises(GeorefError, match="response exceeds configured size limit"):
        GeorefClient(max_response_bytes=32, min_request_interval_seconds=0).list(
            GeorefResource.PROVINCES
        )


def test_georef_client_throttles_to_daily_quota(monkeypatch):
    now = {"value": 0.0}
    sleeps = []

    def fake_monotonic():
        return now["value"]

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now["value"] += seconds

    monkeypatch.setattr("argentina_open_data.sources.georef.time.monotonic", fake_monotonic)
    monkeypatch.setattr("argentina_open_data.sources.georef.time.sleep", fake_sleep)
    monkeypatch.setattr(
        "argentina_open_data.sources.georef.urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            {"provincias": [], "cantidad": 0, "total": 24, "inicio": 0}
        ),
    )
    client = GeorefClient()
    client.list(GeorefResource.PROVINCES)
    client.list(GeorefResource.PROVINCES, offset=10)

    assert sleeps == [9.0]
