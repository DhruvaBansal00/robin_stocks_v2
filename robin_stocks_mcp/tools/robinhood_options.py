"""Robinhood options tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread

Symbols = str | list[str]


@mcp.tool()
@safe_tool()
async def rh_get_aggregate_positions(info: str | None = None, account_number: str | None = None) -> Any:
    """Collapse all option orders for each stock into a single dict per stock."""
    return await to_thread(rh.get_aggregate_positions, info=info, account_number=account_number)


@mcp.tool()
@safe_tool()
async def rh_get_aggregate_open_positions(info: str | None = None, account_number: str | None = None) -> Any:
    """Collapse all open option positions for each stock into a single dict per stock."""
    return await to_thread(rh.get_aggregate_open_positions, info=info, account_number=account_number)


@mcp.tool()
@safe_tool()
async def rh_get_market_options(info: str | None = None) -> Any:
    """Return a list of all market option positions."""
    return await to_thread(rh.get_market_options, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_all_option_positions(info: str | None = None, account_number: str | None = None) -> Any:
    """All option positions ever held for the account."""
    return await to_thread(rh.get_all_option_positions, info=info, account_number=account_number)


@mcp.tool()
@safe_tool()
async def rh_get_open_option_positions(account_number: str | None = None, info: str | None = None) -> Any:
    """All open option positions for the account."""
    return await to_thread(rh.get_open_option_positions, account_number=account_number, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_chains(symbol: str, info: str | None = None) -> Any:
    """Option chain summary information for a ticker."""
    return await to_thread(rh.get_chains, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_find_tradable_options(
    symbol: str,
    expirationDate: str | None = None,
    strikePrice: float | str | None = None,
    optionType: str | None = None,
    info: str | None = None,
) -> Any:
    """List all tradable options for a stock, optionally filtered."""
    return await to_thread(
        rh.find_tradable_options,
        symbol,
        expirationDate=expirationDate,
        strikePrice=strikePrice,
        optionType=optionType,
        info=info,
    )


@mcp.tool()
@safe_tool()
async def rh_find_options_by_expiration(
    inputSymbols: Symbols,
    expirationDate: str,
    optionType: str | None = None,
    info: str | None = None,
) -> Any:
    """Option orders that match an expiration date for the given tickers."""
    return await to_thread(
        rh.find_options_by_expiration,
        inputSymbols,
        expirationDate,
        optionType=optionType,
        info=info,
    )


@mcp.tool()
@safe_tool()
async def rh_find_options_by_strike(
    inputSymbols: Symbols,
    strikePrice: float | str,
    optionType: str | None = None,
    info: str | None = None,
) -> Any:
    """Option orders that match a strike price for the given tickers."""
    return await to_thread(
        rh.find_options_by_strike,
        inputSymbols,
        strikePrice,
        optionType=optionType,
        info=info,
    )


@mcp.tool()
@safe_tool()
async def rh_find_options_by_expiration_and_strike(
    inputSymbols: Symbols,
    expirationDate: str,
    strikePrice: float | str,
    optionType: str | None = None,
    info: str | None = None,
) -> Any:
    """Option orders matching both expiration and strike."""
    return await to_thread(
        rh.find_options_by_expiration_and_strike,
        inputSymbols,
        expirationDate,
        strikePrice,
        optionType=optionType,
        info=info,
    )


@mcp.tool()
@safe_tool()
async def rh_find_options_by_specific_profitability(
    inputSymbols: Symbols,
    expirationDate: str | None = None,
    strikePrice: float | str | None = None,
    optionType: str | None = None,
    typeProfit: str = "chance_of_profit_short",
    profitFloor: float = 0.0,
    profitCeiling: float = 1.0,
    info: str | None = None,
) -> Any:
    """Option market data for tickers within a profitability range."""
    return await to_thread(
        rh.find_options_by_specific_profitability,
        inputSymbols,
        expirationDate=expirationDate,
        strikePrice=strikePrice,
        optionType=optionType,
        typeProfit=typeProfit,
        profitFloor=profitFloor,
        profitCeiling=profitCeiling,
        info=info,
    )


@mcp.tool()
@safe_tool()
async def rh_get_option_market_data_by_id(id: str, info: str | None = None) -> Any:
    """Option market data (greeks, OI, chance of profit, adjusted mark) by id."""
    return await to_thread(rh.get_option_market_data_by_id, id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_option_market_data(
    inputSymbols: Symbols,
    expirationDate: str,
    strikePrice: float | str,
    optionType: str,
    info: str | None = None,
) -> Any:
    """Option market data (greeks, OI, chance of profit) for a specific contract."""
    return await to_thread(
        rh.get_option_market_data,
        inputSymbols,
        expirationDate,
        strikePrice,
        optionType,
        info=info,
    )


@mcp.tool()
@safe_tool()
async def rh_get_option_instrument_data_by_id(id: str, info: str | None = None) -> Any:
    """Option instrument data by id."""
    return await to_thread(rh.get_option_instrument_data_by_id, id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_option_instrument_data(
    symbol: str,
    expirationDate: str,
    strikePrice: float | str,
    optionType: str,
    info: str | None = None,
) -> Any:
    """Option instrument data for a specific contract."""
    return await to_thread(
        rh.get_option_instrument_data,
        symbol,
        expirationDate,
        strikePrice,
        optionType,
        info=info,
    )


@mcp.tool()
@safe_tool()
async def rh_get_option_historicals(
    symbol: str,
    expirationDate: str,
    strikePrice: float | str,
    optionType: str,
    interval: str = "hour",
    span: str = "week",
    bounds: str = "regular",
    info: str | None = None,
) -> Any:
    """Historical price data for an option contract."""
    return await to_thread(
        rh.get_option_historicals,
        symbol,
        expirationDate,
        strikePrice,
        optionType,
        interval=interval,
        span=span,
        bounds=bounds,
        info=info,
    )
