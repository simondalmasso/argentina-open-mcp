"""Public REST API and lightweight server-rendered web entry point."""

from __future__ import annotations

from importlib.resources import files

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from argentina_open_data.registry import list_sources
from argentina_open_data.snapshots import SnapshotStore

app = FastAPI(
    title="Argentina Open Data API",
    version="0.2.0",
    description="Datos públicos argentinos con procedencia y cobertura explícitas.",
)
store = SnapshotStore()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "argentina-open-data"}


@app.get("/api/v1/sources")
async def sources() -> dict:
    return {
        "data": [source.model_dump(mode="json") for source in list_sources()],
        "count": len(list_sources()),
    }


@app.get("/api/v1/snapshots")
async def snapshots() -> dict:
    manifests = store.list_manifests()
    return {
        "data": [manifest.model_dump(mode="json") for manifest in manifests],
        "count": len(manifests),
    }


def _latest_territories(resource: str) -> tuple[list[dict], dict]:
    manifests = tuple(
        item
        for item in store.list_manifests("georef.territories")
        if item.resource == resource
    )
    if not manifests:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "dataset_not_ingested",
                "message": "Todavía no hay un snapshot publicado para este recurso.",
                "resource": resource,
            },
        )
    manifest = manifests[0]
    document = store.load(manifest)
    return (
        [record.territory.model_dump(mode="json") for record in document.records],
        manifest.model_dump(mode="json"),
    )


@app.get("/api/v1/territories")
async def territories(
    resource: str = Query(default="provincias", pattern="^(provincias|departamentos|municipios|localidades)$"),
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    records, manifest = _latest_territories(resource)
    if q:
        needle = q.casefold()
        records = [item for item in records if needle in item["name"].casefold()]
    return {
        "data": records[offset : offset + limit],
        "meta": {"resource": resource, "snapshot": manifest, "total": len(records)},
        "pagination": {"limit": limit, "offset": offset, "returned": len(records)},
    }


@app.get("/api/v1/territories/{geo_id}")
async def territory(geo_id: str) -> dict:
    for resource in ("provincias", "departamentos", "municipios", "localidades"):
        manifests = tuple(
            item
            for item in store.list_manifests("georef.territories")
            if item.resource == resource
        )
        if not manifests:
            continue
        document = store.load(manifests[0])
        for record in document.records:
            if record.territory.geo_id == geo_id:
                return {
                    "data": record.territory.model_dump(mode="json"),
                    "meta": {
                        "snapshot_sha256": manifests[0].snapshot_sha256,
                        "source_id": manifests[0].source_id,
                        "license_id": manifests[0].license_id,
                        "attribution": manifests[0].attribution,
                    },
                }
    raise HTTPException(status_code=404, detail="Territory not found in available snapshots")


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    page = files("argentina_open_data").joinpath("web/index.html").read_text(encoding="utf-8")
    return page
