"""Cloudflare Worker entrypoint: FastAPI REST/web plus stateless MCP."""

from __future__ import annotations

from contextlib import asynccontextmanager

from mcp.server.transport_security import TransportSecuritySettings
from workers import WorkerEntrypoint, asgi

from argentina_open_data import api as api_module
from argentina_open_data import mcp_server as mcp_module
from argentina_open_data.bundled_snapshots import BundledSnapshotStore

# Cloudflare Workers do not provide a persistent local filesystem. The initial,
# reviewed Georef snapshot is shipped as an immutable package resource instead.
store = BundledSnapshotStore()
api_module.store = store
mcp_module.store = store

# The current public target is the existing arg-open.workers.dev Worker.
# Localhost patterns are needed only by local development and CI smoke tests.
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

# Existing REST routes are registered first; the mounted MCP ASGI app handles
# /mcp and leaves the API and homepage routes untouched.
api_module.app.mount("/", mcp_http_app)


@asynccontextmanager
async def lifespan(app):
    # A mounted ASGI sub-application does not own its parent's lifespan.
    # Start the MCP session manager explicitly on the host FastAPI lifespan.
    async with mcp_module.mcp.session_manager.run():
        yield


api_module.app.router.lifespan_context = lifespan


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(api_module.app, request, self.env)
