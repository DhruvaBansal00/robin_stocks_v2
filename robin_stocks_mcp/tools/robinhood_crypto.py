"""Robinhood crypto data tools (read-only)."""

from __future__ import annotations

from typing import Any

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def rh_load_crypto_profile(info: str | None = None) -> Any:
    """Information associated with the crypto account."""
    return await to_thread(rh.load_crypto_profile, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_crypto_positions(info: str | None = None) -> Any:
    """Crypto positions for the account."""
    return await to_thread(rh.get_crypto_positions, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_open_crypto_positions(info: str | None = None) -> Any:
    """Open crypto positions for the account (filters out zero-quantity holdings)."""
    return await to_thread(rh.get_open_crypto_positions, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_crypto_currency_pairs(info: str | None = None) -> Any:
    """All crypto currency pairs available for trading."""
    return await to_thread(rh.get_crypto_currency_pairs, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_crypto_info(symbol: str, info: str | None = None) -> Any:
    """Info for a specific crypto symbol."""
    return await to_thread(rh.get_crypto_info, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_crypto_quote(symbol: str, info: str | None = None) -> Any:
    """Crypto quote: low/high/open price."""
    return await to_thread(rh.get_crypto_quote, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_crypto_quote_from_id(id: str, info: str | None = None) -> Any:
    """Crypto quote by Robinhood crypto id (instead of ticker)."""
    return await to_thread(rh.get_crypto_quote_from_id, id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_crypto_historicals(
    symbol: str,
    interval: str = "hour",
    span: str = "week",
    bounds: str = "24_7",
    info: str | None = None,
) -> Any:
    """Historical OHLC data for a crypto symbol."""
    return await to_thread(rh.get_crypto_historicals, symbol, interval=interval, span=span, bounds=bounds, info=info)
