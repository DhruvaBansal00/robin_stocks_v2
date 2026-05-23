"""Robinhood futures data tools (read-only).

All endpoints used here are undocumented, reverse-engineered against the
Robinhood arsenal/ceres APIs and may break without notice.
"""

from __future__ import annotations

from typing import Any

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread

# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_get_futures_contract(symbol: str, info: str | None = None) -> Any:
    """Return futures-contract details for a single symbol (e.g. 'ESH26')."""
    return await to_thread(rh.get_futures_contract, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_futures_contracts_by_symbols(symbols: list[str], info: str | None = None) -> Any:
    """Return futures-contract details for a list of symbols."""
    return await to_thread(rh.get_futures_contracts_by_symbols, symbols, info=info)


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_get_futures_quote(symbol: str, info: str | None = None) -> Any:
    """Real-time quote for a futures contract by symbol."""
    return await to_thread(rh.get_futures_quote, symbol, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_futures_quotes(symbols: list[str], info: str | None = None) -> Any:
    """Real-time quotes for multiple futures contracts."""
    return await to_thread(rh.get_futures_quotes, symbols, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_futures_quote_by_id(contract_id: str, info: str | None = None) -> Any:
    """Real-time quote by Robinhood contract id."""
    return await to_thread(rh.get_futures_quote_by_id, contract_id, info=info)


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_get_futures_account_id() -> Any:
    """Resolve the user's futures account id (accountType='FUTURES')."""
    return await to_thread(rh.get_futures_account_id)


@mcp.tool()
@safe_tool()
async def rh_get_futures_positions(account_id: str | None = None, info: str | None = None) -> Any:
    """Return current futures positions (positions endpoint is a SDK placeholder for now)."""
    return await to_thread(rh.get_futures_positions, account_id=account_id, info=info)


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_get_all_futures_orders(account_id: str | None = None, info: str | None = None) -> Any:
    """All historical futures orders, automatically paginated."""
    return await to_thread(rh.get_all_futures_orders, account_id=account_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_filled_futures_orders(account_id: str | None = None, info: str | None = None) -> Any:
    """Filled futures orders only, automatically paginated."""
    return await to_thread(rh.get_filled_futures_orders, account_id=account_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_futures_order_info(
    order_id: str,
    account_id: str | None = None,
    info: str | None = None,
) -> Any:
    """Return details for a single futures order by id."""
    return await to_thread(rh.get_futures_order_info, order_id, account_id=account_id, info=info)


# ---------------------------------------------------------------------------
# Pure P&L helpers (no network)
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_extract_futures_pnl(order: dict) -> Any:
    """Pull realized P&L / fees out of one futures order's nested amount fields."""
    return await to_thread(rh.extract_futures_pnl, order)


@mcp.tool()
@safe_tool()
async def rh_calculate_total_futures_pnl(orders: list[dict]) -> Any:
    """Aggregate realized P&L / fees across a list of futures orders. Only counts CLOSING orders."""
    return await to_thread(rh.calculate_total_futures_pnl, orders)
