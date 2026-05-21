"""TD Ameritrade order tools."""

from __future__ import annotations

from typing import Any, Optional

import robin_stocks.tda as tda

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool(write=True)
async def tda_place_order(
    account_id: str, order_payload: dict, jsonify: Optional[bool] = None
) -> Any:
    """Place an order on a TDA account. `order_payload` follows the TDA Orders API schema."""
    return await to_thread(tda.place_order, account_id, order_payload, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def tda_cancel_order(
    account_id: str, order_id: str, jsonify: Optional[bool] = None
) -> Any:
    """Cancel an existing TDA order."""
    return await to_thread(tda.cancel_order, account_id, order_id, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_order(
    account_id: str, order_id: str, jsonify: Optional[bool] = None
) -> Any:
    """Get information about a single TDA order."""
    return await to_thread(tda.get_order, account_id, order_id, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_orders_for_account(
    account_id: str,
    max_results: Optional[int] = None,
    from_time: Optional[str] = None,
    to_time: Optional[str] = None,
    status: Optional[str] = None,
    jsonify: Optional[bool] = None,
) -> Any:
    """List orders on a TDA account, optionally filtered."""
    return await to_thread(
        tda.get_orders_for_account,
        account_id,
        max_results=max_results,
        from_time=from_time,
        to_time=to_time,
        status=status,
        jsonify=jsonify,
    )
