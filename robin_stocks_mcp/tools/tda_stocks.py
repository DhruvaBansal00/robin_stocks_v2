"""TD Ameritrade stock-data tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.tda as tda

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def tda_get_quote(ticker: str, jsonify: bool | None = None) -> Any:
    """Quote info for a single stock via TDA."""
    return await to_thread(tda.get_quote, ticker, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_quotes(tickers: str | list[str], jsonify: bool | None = None) -> Any:
    """Quote info for multiple stocks via TDA."""
    return await to_thread(tda.get_quotes, tickers, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_price_history(
    ticker: str,
    period_type: str,
    frequency_type: str,
    frequency: str,
    period: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    needExtendedHoursData: bool = True,
    jsonify: bool | None = None,
) -> Any:
    """Price history for a stock.

    period_type: day / month / year / ytd
    frequency_type: minute / daily / weekly / monthly
    """
    return await to_thread(
        tda.get_price_history,
        ticker,
        period_type,
        frequency_type,
        frequency,
        period=period,
        start_date=start_date,
        end_date=end_date,
        needExtendedHoursData=needExtendedHoursData,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool()
async def tda_search_instruments(ticker_string: str, projection: str, jsonify: bool | None = None) -> Any:
    """Search instruments matching a ticker string. projection: symbol-search / symbol-regex / desc-search / desc-regex / fundamental."""
    return await to_thread(tda.search_instruments, ticker_string, projection, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_instrument(cusip: str, jsonify: bool | None = None) -> Any:
    """Get instrument data by CUSIP."""
    return await to_thread(tda.get_instrument, cusip, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_option_chains(
    ticker: str,
    contract_type: str = "ALL",
    strike_count: str = "10",
    include_quotes: str = "FALSE",
    strategy: str = "SINGLE",
    interval: str | None = None,
    strike_price: str | None = None,
    range_value: str = "ALL",
    from_date: str | None = None,
    to_date: str | None = None,
    volatility: str | None = None,
    underlying_price: str | None = None,
    interest_rate: str | None = None,
    days_to_expiration: str | None = None,
    exp_month: str = "ALL",
    option_type: str = "ALL",
    jsonify: bool | None = None,
) -> Any:
    """Option chain data for a stock via TDA."""
    return await to_thread(
        tda.get_option_chains,
        ticker,
        contract_type=contract_type,
        strike_count=strike_count,
        include_quotes=include_quotes,
        strategy=strategy,
        interval=interval,
        strike_price=strike_price,
        range_value=range_value,
        from_date=from_date,
        to_date=to_date,
        volatility=volatility,
        underlying_price=underlying_price,
        interest_rate=interest_rate,
        days_to_expiration=days_to_expiration,
        exp_month=exp_month,
        option_type=option_type,
        jsonify=jsonify,
    )
