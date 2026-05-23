"""Robinhood stock-data tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread

Symbols = str | list[str]


@mcp.tool()
@safe_tool()
async def rh_get_quotes(inputSymbols: Symbols, info: str | None = None) -> Any:
    """Quote info (bid/ask/last price/volume) for one or more tickers."""
    return await to_thread(rh.get_quotes, inputSymbols, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_fundamentals(inputSymbols: Symbols, info: str | None = None) -> Any:
    """Fundamentals for one or more tickers: sector, description, dividend yield, market cap."""
    return await to_thread(rh.get_fundamentals, inputSymbols, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_instruments_by_symbols(inputSymbols: Symbols, info: str | None = None) -> Any:
    """Instrument metadata held by the market (bloomberg id, listing date, etc.)."""
    return await to_thread(rh.get_instruments_by_symbols, inputSymbols, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_instrument_by_url(url: str, info: str | None = None) -> Any:
    """Instrument data given the canonical instrument URL."""
    return await to_thread(rh.get_instrument_by_url, url, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_latest_price(
    inputSymbols: Symbols,
    priceType: str | None = None,
    includeExtendedHours: bool = True,
) -> Any:
    """Latest price for each ticker, returned as a list of strings."""
    return await to_thread(rh.get_latest_price, inputSymbols, priceType=priceType, includeExtendedHours=includeExtendedHours)


@mcp.tool()
@safe_tool()
async def rh_get_name_by_symbol(symbol: str) -> Any:
    """Stock name from the ticker."""
    return await to_thread(rh.get_name_by_symbol, symbol)


@mcp.tool()
@safe_tool()
async def rh_get_name_by_url(url: str) -> Any:
    """Stock name from the instrument URL."""
    return await to_thread(rh.get_name_by_url, url)


@mcp.tool()
@safe_tool()
async def rh_get_symbol_by_url(url: str) -> Any:
    """Stock symbol from the instrument URL."""
    return await to_thread(rh.get_symbol_by_url, url)


@mcp.tool()
@safe_tool()
async def rh_get_ratings(symbol: str, info: str | None = None) -> Any:
    """Analyst ratings (buy/hold/sell counts) for a stock."""
    return await to_thread(rh.get_ratings, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_events(symbol: str, info: str | None = None) -> Any:
    """Events related to a stock that the user owns."""
    return await to_thread(rh.get_events, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_earnings(symbol: str, info: str | None = None) -> Any:
    """Earnings reports for the different financial quarters."""
    return await to_thread(rh.get_earnings, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_news(symbol: str, info: str | None = None) -> Any:
    """News stories for a stock."""
    return await to_thread(rh.get_news, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_splits(symbol: str, info: str | None = None) -> Any:
    """Stock splits (date, divisor, multiplier)."""
    return await to_thread(rh.get_splits, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_find_instrument_data(query: str) -> Any:
    """Search for instruments matching the query keyword."""
    return await to_thread(rh.find_instrument_data, query)


@mcp.tool()
@safe_tool()
async def rh_get_stock_historicals(
    inputSymbols: Symbols,
    interval: str = "hour",
    span: str = "week",
    bounds: str = "regular",
    info: str | None = None,
) -> Any:
    """Historical OHLC for stocks. interval: 5/10minute, hour, day, week. span: day..5year, all."""
    return await to_thread(rh.get_stock_historicals, inputSymbols, interval=interval, span=span, bounds=bounds, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_stock_quote_by_id(stock_id: str, info: str | None = None) -> Any:
    """Quote info for a single stock by Robinhood instrument id."""
    return await to_thread(rh.get_stock_quote_by_id, stock_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_index_quote_by_id(stock_id: str, info: str | None = None) -> Any:
    """Quote info for an index-option underlying (SPX, NDX, etc.) by Robinhood index id."""
    return await to_thread(rh.get_index_quote_by_id, stock_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_stock_quote_by_symbol(symbol: str, info: str | None = None) -> Any:
    """Quote info for a single stock by ticker symbol."""
    return await to_thread(rh.get_stock_quote_by_symbol, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_pricebook_by_id(stock_id: str, info: str | None = None) -> Any:
    """Order pricebook (level-2 quotes) by instrument id. Requires Robinhood Gold."""
    return await to_thread(rh.get_pricebook_by_id, stock_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_pricebook_by_symbol(symbol: str, info: str | None = None) -> Any:
    """Order pricebook (level-2 quotes) by symbol. Requires Robinhood Gold."""
    return await to_thread(rh.get_pricebook_by_symbol, symbol, info=info)
