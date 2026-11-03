"""Cloudflare Worker entrypoint with lazy, request-time MCP initialization.

MCPServer creates an ephemeral signing key with os.urandom() at construction.
Cloudflare intentionally blocks entropy during module initialization because
startup values can be snapshotted and repeated across isolates. The MCP module
and FastAPI/MCP composition are therefore created on the first incoming request,
after the Worker runtime is active.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from workers import WorkerEntrypoint, asgi

_app = None


def _get_app():
    global _app
    if _app is not None:
        return _app

    # Import only after the first request enters the running Worker. Importing
    # mcp_server constructs MCPServer, which needs runtime entropy.
    from mcp.server.transport_security import TransportSecuritySettings

    from argentina_open_data import api as api_module
    from argentina_open_data import mcp_server as mcp_module
    from argentina_open_data.bundled_snapshots import BundledSnapshotStore

    store = BundledSnapshotStore()
    api_module.store = store
    mcp_module.store = store

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
    mcp_http_app = mcp_module.mcp.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=security,
    )

    # FastAPI owns the host lifespan. A mounted sub-application does not run
    # its own lifespan, so explicitly start MCP's session manager here.
    @asynccontextmanager
    async def lifespan(app):
        async with mcp_module.mcp.session_manager.run():
            yield

    api_module.app.router.lifespan_context = lifespan

    # Keep the public web and REST routes first; /mcp is handled by the mount.
    api_module.app.mount("/", mcp_http_app)
    _app = api_module.app
    return _app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(_get_app(), request, self.env)
