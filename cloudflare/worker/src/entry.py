"""Cloudflare Worker entrypoint: FastAPI REST/web and stateless MCP."""

from __future__ import annotations

from urllib.parse import urlsplit

from workers import WorkerEntrypoint, asgi

_store = None


def _get_app(request):
    global _store

    # Cloudflare Workers prohibit entropy during module initialization because
    # startup memory is snapshotted. Defer application imports to the first
    # request, where the runtime RNG is available.
    from argentina_open_data import api as api_module
    from argentina_open_data.bundled_snapshots import BundledSnapshotStore

    if _store is None:
        _store = BundledSnapshotStore()
    api_module.store = _store

    # Ordinary website and REST requests never construct or start an MCP server.
    # MCP is stateless/read-only, so create a fresh server and ASGI lifespan only
    # for a request addressed to the MCP endpoint.
    request_path = urlsplit(request.url).path
    if request_path in {"/mcp", "/mcp/"}:
        from argentina_open_data import mcp_server as mcp_module
        from mcp.server.transport_security import TransportSecuritySettings

        mcp_module.store = _store
        server = mcp_module.create_mcp_server()
        security = TransportSecuritySettings(
            allowed_hosts=[
                "arg-open.simondalmasso44.workers.dev",
                "arg-open.simondalmasso44.workers.dev:*",
                "127.0.0.1:*",
                "localhost:*",
            ],
            allowed_origins=[
                "https://arg-open.simondalmasso44.workers.dev",
                "http://127.0.0.1:*",
                "http://localhost:*",
            ],
        )
        return server.streamable_http_app(
            stateless_http=True,
            json_response=True,
            transport_security=security,
            streamable_http_path=request_path,
        )

    return api_module.app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(_get_app(request), request, self.env)
