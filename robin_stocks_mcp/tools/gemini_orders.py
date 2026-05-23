"""Gemini order tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.gemini as gem

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def gem_get_trades_for_crypto(
    ticker: str,
    limit_trades: int = 50,
    timestamp: str | None = None,
    jsonify: bool | None = None,
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
async def gem_active_orders(jsonify: bool | None = None) -> Any:
    """All active Gemini orders."""
    return await to_thread(gem.active_orders, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_order_status(order_id: str, jsonify: bool | None = None) -> Any:
    """Status of a specific Gemini order."""
    return await to_thread(gem.order_status, order_id, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_cancel_order(order_id: str, jsonify: bool | None = None) -> Any:
    """Cancel a specific Gemini order."""
    return await to_thread(gem.cancel_order, order_id, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_cancel_all_session_orders(jsonify: bool | None = None) -> Any:
    """Cancel all orders opened by the current Gemini session."""
    return await to_thread(gem.cancel_all_session_orders, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_cancel_all_active_orders(jsonify: bool | None = None) -> Any:
    """Cancel all Gemini orders for the account."""
    return await to_thread(gem.cancel_all_active_orders, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float | None = None,
    order_type: str = "exchange limit",
    options: list | None = None,
    jsonify: bool | None = None,
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
async def gem_order_market(symbol: str, side: str, quantity: float, jsonify: bool | None = None) -> Any:
    """Submit a market order on Gemini."""
    return await to_thread(gem.order_market, symbol, side, quantity, jsonify=jsonify)
