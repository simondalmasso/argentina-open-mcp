"""MCP tools backed only by admitted, locally stored snapshots."""

from __future__ import annotations

import os

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from argentina_open_data.registry import list_sources
from argentina_open_data.snapshots import SnapshotStore

store = SnapshotStore()


async def list_data_sources() -> dict:
    """List registered Argentine public-data sources, license status and evidence."""
    return {
        "sources": [source.model_dump(mode="json") for source in list_sources()]
    }


async def search_territories(
    query: str = "",
    resource: str = "provincias",
    limit: int = 20,
) -> dict:
    """Search territories in verified local snapshots; does not call external APIs."""
    if resource not in {"provincias", "departamentos", "municipios", "localidades"}:
        return {"error": "unsupported_resource"}
    if not 1 <= limit <= 100:
        return {"error": "limit_must_be_between_1_and_100"}
    manifests = tuple(
        item
        for item in store.list_manifests("georef.territories")
        if item.resource == resource
    )
    if not manifests:
        return {
            "error": "dataset_not_ingested",
            "message": "No published snapshot is available for this resource yet.",
        }
    manifest = manifests[0]
    document = store.load(manifest)
    needle = query.casefold().strip()
    matches = [
        record.territory.model_dump(mode="json")
        for record in document.records
        if needle in record.territory.name.casefold()
    ][:limit]
    return {
        "data": matches,
        "meta": {
            "resource": resource,
            "snapshot_sha256": manifest.snapshot_sha256,
            "license_id": manifest.license_id,
            "attribution": manifest.attribution,
            "total_matches_returned": len(matches),
        },
    }


async def get_territory(geo_id: str) -> dict:
    """Retrieve one territory by its official Georef identifier from local snapshots."""
    if not geo_id or len(geo_id) > 100:
        return {"error": "invalid_geo_id"}
    for manifest in store.list_manifests("georef.territories"):
        document = store.load(manifest)
        for record in document.records:
            if record.territory.geo_id == geo_id:
                return {
                    "data": record.territory.model_dump(mode="json"),
                    "meta": {
                        "snapshot_sha256": manifest.snapshot_sha256,
                        "license_id": manifest.license_id,
                        "attribution": manifest.attribution,
                    },
                }
    return {"error": "territory_not_found"}


def create_mcp_server() -> MCPServer:
    """Create a fresh stateless server instance for one Worker request.

    Cloudflare's ASGI adapter starts and stops application lifespan for each
    request. StreamableHTTPSessionManager.run() is single-use, so each request
    gets its own stateless server/session manager instead of reusing one.
    """
    server = MCPServer("Argentina Open MCP")
    server.tool()(list_data_sources)
    server.tool()(search_territories)
    server.tool()(get_territory)
    return server


def run() -> None:
    """Run the standalone stateful process outside the Cloudflare Worker runtime."""
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8001"))
    if host in {"127.0.0.1", "localhost", "::1"}:
        security = TransportSecuritySettings(
            allowed_hosts=[f"{host}:*", "localhost:*", "127.0.0.1:*", "[::1]:*"],
            allowed_origins=["http://localhost:*", "http://127.0.0.1:*", "http://[::1]:*"],
        )
    else:
        allowed_hosts = [value.strip() for value in os.getenv("MCP_ALLOWED_HOSTS", "").split(",") if value.strip()]
        allowed_origins = [value.strip() for value in os.getenv("MCP_ALLOWED_ORIGINS", "").split(",") if value.strip()]
        if not allowed_hosts:
            raise RuntimeError("MCP_ALLOWED_HOSTS is required when MCP_HOST is not localhost")
        security = TransportSecuritySettings(
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )
    create_mcp_server().run(
        transport="streamable-http",
        host=host,
        port=port,
        transport_security=security,
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    run()
