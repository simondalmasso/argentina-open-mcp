"""Cloudflare-compatible ASGI handlers must not require worker threads."""

import inspect

from argentina_open_data import api, mcp_server


def test_public_rest_handlers_are_async():
    handlers = (
        api.health,
        api.sources,
        api.snapshots,
        api.territories,
        api.territory,
        api.home,
    )

    assert all(inspect.iscoroutinefunction(handler) for handler in handlers)


def test_mcp_tool_handlers_are_async():
    handlers = (
        mcp_server.list_data_sources,
        mcp_server.search_territories,
        mcp_server.get_territory,
    )

    assert all(inspect.iscoroutinefunction(handler) for handler in handlers)
