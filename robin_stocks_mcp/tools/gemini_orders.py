"""Gemini order tools."""

from __future__ import annotations

from typing import Any, Optional

import robin_stocks.gemini as gem

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def gem_get_trades_for_crypto(
    ticker: str,
    limit_trades: int = 50,
    timestamp: Optional[str] = None,
    jsonify: Optional[bool] = None,
) -> Any:
    """Trade history for a Gemini symbol."""
    return await to_thread(
        gem.get_trades_for_crypto,
        ticker,
        limit_trades=limit_trades,
        timestamp=timestamp,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool()
async def gem_active_orders(jsonify: Optional[bool] = None) -> Any:
    """All active Gemini orders."""
    return await to_thread(gem.active_orders, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_order_status(order_id: str, jsonify: Optional[bool] = None) -> Any:
    """Status of a specific Gemini order."""
    return await to_thread(gem.order_status, order_id, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_cancel_order(order_id: str, jsonify: Optional[bool] = None) -> Any:
    """Cancel a specific Gemini order."""
    return await to_thread(gem.cancel_order, order_id, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_cancel_all_session_orders(jsonify: Optional[bool] = None) -> Any:
    """Cancel all orders opened by the current Gemini session."""
    return await to_thread(gem.cancel_all_session_orders, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_cancel_all_active_orders(jsonify: Optional[bool] = None) -> Any:
    """Cancel all Gemini orders for the account."""
    return await to_thread(gem.cancel_all_active_orders, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_order(
    symbol: str,
    side: str,
    quantity: float,
    price: Optional[float] = None,
    order_type: str = "exchange limit",
    options: Optional[list] = None,
    jsonify: Optional[bool] = None,
) -> Any:
    """Submit a Gemini order. side: 'buy'/'sell'. order_type defaults to 'exchange limit'."""
    return await to_thread(
        gem.order,
        symbol,
        side,
        quantity,
        price=price,
        order_type=order_type,
        options=options,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def gem_order_market(
    symbol: str, side: str, quantity: float, jsonify: Optional[bool] = None
) -> Any:
    """Submit a market order on Gemini."""
    return await to_thread(gem.order_market, symbol, side, quantity, jsonify=jsonify)
