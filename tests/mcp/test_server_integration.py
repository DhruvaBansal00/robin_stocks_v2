"""Higher-level integration test: exercise the FastMCP request handlers end-to-end.

We don't open a stdio pipe — instead we call FastMCP's `list_tools` and `call_tool` methods
directly. That mirrors what the MCP server does under the hood when a client connects.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from robin_stocks_mcp.app import mcp


@pytest.mark.asyncio
async def test_list_tools_via_fastmcp() -> None:
    """`mcp.list_tools()` is the public method the MCP protocol uses."""
    tools = await mcp.list_tools()
    names = [t.name for t in tools]
    assert "rh_get_quotes" in names
    assert "tda_get_quote" in names
    assert "gem_get_pubticker" in names
    # No internal helpers leaked into the tool surface
    assert "filter_data" not in names
    assert "request_get" not in names


@pytest.mark.asyncio
async def test_call_tool_via_fastmcp_with_mocked_sdk() -> None:
    """`mcp.call_tool()` is what the protocol dispatches to.

    FastMCP returns either a list of `Content` blocks or a tuple of
    (content_blocks, structured_payload) depending on version. Either way our SDK
    return value must appear somewhere in the serialized output.
    """
    with patch("robin_stocks.robinhood.get_quotes", return_value=[{"symbol": "AAPL", "last": "1"}]):
        result = await mcp.call_tool("rh_get_quotes", {"inputSymbols": "AAPL"})

    serialized = json.dumps(result, default=str)
    assert "AAPL" in serialized


@pytest.mark.asyncio
async def test_call_tool_unknown_name_errors() -> None:
    """Calling a nonexistent tool through FastMCP raises (the SDK handles it)."""
    with pytest.raises(ToolError):
        await mcp.call_tool("does_not_exist_xyz", {})


@pytest.mark.asyncio
async def test_call_write_tool_blocked_read_only(writes_disabled) -> None:
    """Write tools return structured error payloads, not exceptions."""
    with patch("robin_stocks.robinhood.order_buy_market") as m:
        result = await mcp.call_tool("rh_order_buy_market", {"symbol": "AAPL", "quantity": 1})
        m.assert_not_called()

    # Confirm error markers appear in serialized result
    serialized = json.dumps(result, default=str)
    assert "ReadOnlyError" in serialized
