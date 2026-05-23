"""TD Ameritrade account tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.tda as tda

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def tda_get_accounts(options: str | None = None, jsonify: bool | None = None) -> Any:
    """Get all TDA accounts. `options`: comma-separated 'positions,orders'."""
    return await to_thread(tda.get_accounts, options=options, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_account(id: str, options: str | None = None, jsonify: bool | None = None) -> Any:
    """Get account information for a specific TDA account id."""
    return await to_thread(tda.get_account, id, options=options, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_transactions(
    id: str,
    type_value: str | None = None,
    symbol: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    jsonify: bool | None = None,
) -> Any:
    """Transactions for a TDA account, optionally filtered by type, symbol, date range."""
    return await to_thread(
        tda.get_transactions,
        id,
        type_value=type_value,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool()
async def tda_get_transaction(account_id: str, transaction_id: str, jsonify: bool | None = None) -> Any:
    """Get information for a single TDA transaction."""
    return await to_thread(tda.get_transaction, account_id, transaction_id, jsonify=jsonify)
