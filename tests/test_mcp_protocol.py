import anyio
import json
from mcp import Client

from argentina_open_data import mcp_server


def test_mcp_protocol_lists_and_invokes_tools():
    async def exercise():
        async with Client(mcp_server.mcp) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert {
                "list_data_sources",
                "search_territories",
                "get_territory",
            } <= names
            result = await client.call_tool("list_data_sources", {})
            assert result.content
            payload = json.loads(result.content[0].text)
            source_ids = {item["source_id"] for item in payload["sources"]}
            assert "georef.territories" in source_ids

    anyio.run(exercise)
