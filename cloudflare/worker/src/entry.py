"""Cloudflare Worker entrypoint: REST/web plus stateless MCP."""

from __future__ import annotations

from contextlib import asynccontextmanager

from workers import WorkerEntrypoint, asgi

_store = None


def _get_app():
    global _store

    # Python Workers prohibit entropy during module initialization because their
    # startup memory is snapshotted. Defer imports and MCPServer construction to
    # the request handler, where a cryptographically secure runtime RNG is ready.
    from starlette.applications import Starlette
    from starlette.routing import Mount

    from argentina_open_data import api as api_module
    from argentina_open_data import mcp_server as mcp_module
    from argentina_open_data.bundled_snapshots import BundledSnapshotStore
    from mcp.server.transport_security import TransportSecuritySettings

    if _store is None:
        _store = BundledSnapshotStore()
    api_module.store = _store
    mcp_module.store = _store

    # The MCP SDK's session manager can only run once per instance. The Cloudflare
    # ASGI adapter owns lifespan per request, so use a fresh stateless server for
    # each request. No MCP session state is required by this read-only API.
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
    mcp_http_app = server.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=security,
        streamable_http_path="/",
    )

    @asynccontextmanager
    async def lifespan(app):
        async with server.session_manager.run():
            yield

    # Route MCP first. The path "/" on the child app makes the public endpoint
    # exactly /mcp; the API FastAPI app handles all remaining routes.
    return Starlette(
        routes=[
            Mount("/mcp", app=mcp_http_app),
            Mount("/", app=api_module.app),
        ],
        lifespan=lifespan,
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(_get_app(), request, self.env)
