"""Read-only client for Argentina's official Georef API v2.0."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import StrEnum
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from argentina_open_data.contracts import GeoLevel, Territory


class GeorefResource(StrEnum):
    PROVINCES = "provincias"
    DEPARTMENTS = "departamentos"
    MUNICIPALITIES = "municipios"
    LOCALITIES = "localidades"


_RESOURCE_LEVELS = {
    GeorefResource.PROVINCES: GeoLevel.PROVINCE,
    GeorefResource.DEPARTMENTS: GeoLevel.DEPARTMENT,
    GeorefResource.MUNICIPALITIES: GeoLevel.MUNICIPALITY,
    GeorefResource.LOCALITIES: GeoLevel.LOCALITY,
}


class GeorefError(RuntimeError):
    """Raised when the official Georef service returns an unusable response."""


@dataclass(frozen=True)
class GeorefRecord:
    id: str
    name: str
    resource: GeorefResource
    payload: dict

    def to_territory(self) -> Territory:
        parent_id = None
        for parent_key in ("departamento", "municipio", "provincia"):
            parent = self.payload.get(parent_key)
            if isinstance(parent, dict) and parent.get("id") is not None:
                parent_id = str(parent["id"])
                break
        return Territory(
            geo_id=self.id,
            name=self.name,
            level=_RESOURCE_LEVELS[self.resource],
            parent_geo_id=parent_id,
            source_system="georef-v2",
        )


@dataclass(frozen=True)
class GeorefPage:
    records: tuple[GeorefRecord, ...]
    count: int
    total: int
    offset: int
    resource: GeorefResource


class GeorefClient:
    """Small bounded client; callers control pagination and request cadence."""

    BASE_URL = "https://apis.datos.gob.ar/georef/api/v2.0"
    LICENSE_ID = "CC-BY-4.0"
    ATTRIBUTION = "Servicio Georef – https://www.argentina.gob.ar/georef"

    def __init__(
        self,
        timeout: float = 10.0,
        max_response_bytes: int = 5_000_000,
        min_request_interval_seconds: float = 9.0,
    ):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")
        if min_request_interval_seconds < 0:
            raise ValueError("min_request_interval_seconds cannot be negative")
        self.timeout = timeout
        self.max_response_bytes = max_response_bytes
        self.min_request_interval_seconds = min_request_interval_seconds
        self._last_request_at: float | None = None

    def list(
        self,
        resource: GeorefResource,
        *,
        limit: int = 100,
        offset: int = 0,
        province_id: str | None = None,
    ) -> GeorefPage:
        if not isinstance(resource, GeorefResource):
            raise ValueError("resource must be a supported GeorefResource")
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        if province_id is not None:
            if resource == GeorefResource.PROVINCES:
                raise ValueError("province_id cannot filter the provinces resource")
            if not province_id.isdigit():
                raise ValueError("province_id must contain only digits")

        params = {"max": limit, "inicio": offset}
        if province_id is not None:
            params["provincia"] = province_id
        url = f"{self.BASE_URL}/{resource.value}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "ArgentinaOpenData/0.1 (+https://github.com/simondalmasso/argentina-open-mcp)",
            },
            method="GET",
        )
        if self._last_request_at is not None and self.min_request_interval_seconds:
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self.min_request_interval_seconds:
                time.sleep(self.min_request_interval_seconds - elapsed)
        self._last_request_at = time.monotonic()

        try:
            with urlopen(request, timeout=self.timeout) as response:
                status = getattr(response, "status", 200)
                if status < 200 or status >= 300:
                    raise GeorefError(f"Georef returned HTTP {status}")
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > self.max_response_bytes:
                    raise GeorefError("response exceeds configured size limit")
                raw = response.read(self.max_response_bytes + 1)
        except GeorefError:
            raise
        except HTTPError as exc:
            raise GeorefError(f"Georef returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise GeorefError(f"Georef request failed: {exc}") from exc

        if len(raw) > self.max_response_bytes:
            raise GeorefError("response exceeds configured size limit")
        try:
            document = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GeorefError("Georef response is not valid UTF-8 JSON") from exc
        if not isinstance(document, dict) or not isinstance(document.get(resource.value), list):
            raise GeorefError(f"missing expected result collection: {resource.value}")

        records = []
        for item in document[resource.value]:
            if not isinstance(item, dict) or item.get("id") is None or not item.get("nombre"):
                raise GeorefError("Georef returned a record without an id or name")
            records.append(
                GeorefRecord(
                    id=str(item["id"]),
                    name=str(item["nombre"]),
                    resource=resource,
                    payload=item,
                )
            )

        count = document.get("cantidad", len(records))
        total = document.get("total", count)
        returned_offset = document.get("inicio", offset)
        if not all(isinstance(value, int) and value >= 0 for value in (count, total, returned_offset)):
            raise GeorefError("Georef returned invalid pagination metadata")
        return GeorefPage(
            records=tuple(records),
            count=count,
            total=total,
            offset=returned_offset,
            resource=resource,
        )
