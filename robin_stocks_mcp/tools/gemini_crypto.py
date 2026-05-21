"""Gemini crypto market-data tools."""

from __future__ import annotations

from typing import Any, Optional

import robin_stocks.gemini as gem

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def gem_get_pubticker(ticker: str, jsonify: Optional[bool] = None) -> Any:
    """Public ticker info (bid/ask/last) for a Gemini symbol (e.g. 'btcusd')."""
    return await to_thread(gem.get_pubticker, ticker, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_get_ticker(ticker: str, jsonify: Optional[bool] = None) -> Any:
    """Recent trade info for a Gemini symbol."""
    return await to_thread(gem.get_ticker, ticker, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_get_symbols(jsonify: Optional[bool] = None) -> Any:
    """All tradable Gemini symbols."""
    return await to_thread(gem.get_symbols, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_get_symbol_details(ticker: str, jsonify: Optional[bool] = None) -> Any:
    """Detailed info about a single Gemini symbol."""
    return await to_thread(gem.get_symbol_details, ticker, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_get_price(ticker: str, jsonify: Optional[bool] = None) -> Any:
    """Current price for a Gemini symbol."""
    return await to_thread(gem.get_price, ticker, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_get_notional_volume(jsonify: Optional[bool] = None) -> Any:
    """Account notional volume info."""
    return await to_thread(gem.get_notional_volume, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_get_trade_volume(jsonify: Optional[bool] = None) -> Any:
    """Account trade volume info."""
    return await to_thread(gem.get_trade_volume, jsonify=jsonify)
