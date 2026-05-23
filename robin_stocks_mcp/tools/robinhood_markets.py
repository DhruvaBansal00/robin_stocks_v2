"""Robinhood market data tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def rh_get_top_movers_sp500(direction: str, info: str | None = None) -> Any:
    """Top S&P500 movers for the day. direction: 'up' or 'down'."""
    return await to_thread(rh.get_top_movers_sp500, direction, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_top_100(info: str | None = None) -> Any:
    """Top 100 stocks on Robinhood."""
    return await to_thread(rh.get_top_100, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_top_movers(info: str | None = None) -> Any:
    """Top 20 movers on Robinhood."""
    return await to_thread(rh.get_top_movers, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_all_stocks_from_market_tag(tag: str, info: str | None = None) -> Any:
    """Stocks matching a category tag (e.g. 'technology', 'finance')."""
    return await to_thread(rh.get_all_stocks_from_market_tag, tag, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_markets(info: str | None = None) -> Any:
    """List of available markets."""
    return await to_thread(rh.get_markets, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_market_today_hours(market: str, info: str | None = None) -> Any:
    """Today's open/close hours for a specific market."""
    return await to_thread(rh.get_market_today_hours, market, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_market_next_open_hours(market: str, info: str | None = None) -> Any:
    """Next open day's hours for a specific market."""
    return await to_thread(rh.get_market_next_open_hours, market, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_market_next_open_hours_after_date(market: str, date: str, info: str | None = None) -> Any:
    """Next open day's hours after a given date (YYYY-MM-DD)."""
    return await to_thread(rh.get_market_next_open_hours_after_date, market, date, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_market_hours(market: str, date: str, info: str | None = None) -> Any:
    """Open/close hours for a market on a specific date (YYYY-MM-DD)."""
    return await to_thread(rh.get_market_hours, market, date, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_currency_pairs(info: str | None = None) -> Any:
    """Available currency pairs."""
    return await to_thread(rh.get_currency_pairs, info=info)
