"""Robinhood prediction-market (event-contract) tools.

Browsing/read tools are safe; order placement and cancellation are
write-guarded. All endpoints are undocumented, reverse-engineered against the
Robinhood prediction-markets/ceres APIs and may break without notice.
"""

from __future__ import annotations

from typing import Any

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread

# ---------------------------------------------------------------------------
# Browse (read)
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_get_prediction_market_categories(info: str | None = None) -> Any:
    """List prediction-market categories (e.g. 'Crypto', 'Soccer', 'Politics')."""
    return await to_thread(rh.get_prediction_market_categories, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_prediction_market_events(category: str, info: str | None = None) -> Any:
    """List prediction-market events for a category display name (e.g. 'Crypto')."""
    return await to_thread(rh.get_prediction_market_events, category, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_prediction_markets(category: str, info: str | None = None) -> Any:
    """List the markets shown under a category the way the app's hub displays them.

    Robust for any tab (e.g. 'Pro basketball', 'Featured') and surfaces live in-game
    markets. Accepts a category display name or a navigation node ID.
    """
    return await to_thread(rh.get_prediction_markets, category, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_prediction_market_event(event_id: str, info: str | None = None) -> Any:
    """Return details for a single prediction-market event by id."""
    return await to_thread(rh.get_prediction_market_event, event_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_event_contract(contract_id: str, info: str | None = None) -> Any:
    """Return details for a single event contract by id."""
    return await to_thread(rh.get_event_contract, contract_id, info=info)


# ---------------------------------------------------------------------------
# Account / positions / orders (read)
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_get_event_contracts_account_id() -> Any:
    """Resolve the derivatives account id used for event contracts (accountType='SWAP')."""
    return await to_thread(rh.get_event_contracts_account_id)


@mcp.tool()
@safe_tool()
async def rh_get_event_contract_positions(account_id: str | None = None, info: str | None = None) -> Any:
    """Return current event-contract positions."""
    return await to_thread(rh.get_event_contract_positions, account_id=account_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_event_contract_orders(account_id: str | None = None, info: str | None = None) -> Any:
    """Return event-contract orders, automatically paginated."""
    return await to_thread(rh.get_event_contract_orders, account_id=account_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_event_contract_order_info(
    order_id: str,
    account_id: str | None = None,
    info: str | None = None,
) -> Any:
    """Return details for a single event-contract order by id."""
    return await to_thread(rh.get_event_contract_order_info, order_id, account_id=account_id, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_event_contract_order_fees(
    contract_id: str,
    side: str,
    quantity: float,
    limit_price: float,
    account_id: str | None = None,
    info: str | None = None,
) -> Any:
    """Preview fees for an event-contract order WITHOUT placing it."""
    return await to_thread(
        rh.get_event_contract_order_fees,
        contract_id,
        side,
        quantity,
        limit_price,
        account_id=account_id,
        info=info,
    )


# ---------------------------------------------------------------------------
# Trade (write-guarded)
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool(write=True)
async def rh_order_event_contract(
    contract_id: str,
    side: str,
    quantity: float,
    limit_price: float,
    client_marketdata: dict,
    quote_id: str,
    account_id: str | None = None,
    time_in_force: str = "GTC",
    ref_id: str | None = None,
    info: str | None = None,
) -> Any:
    """Place an event-contract order. side='BUY' to open or 'SELL' to close.

    Requires a live quote: client_marketdata (bid/ask/timestamp wrapped as {"value": ...})
    and quote_id. Robinhood streams these over a websocket the SDK does not yet implement,
    so the caller must supply them; the server rejects stale/fabricated prices.
    """
    return await to_thread(
        rh.order_event_contract,
        contract_id,
        side,
        quantity,
        limit_price,
        client_marketdata,
        quote_id,
        account_id=account_id,
        time_in_force=time_in_force,
        ref_id=ref_id,
        info=info,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_cancel_event_contract_order(order_id: str, info: str | None = None) -> Any:
    """Cancel an event-contract order by id."""
    return await to_thread(rh.cancel_event_contract_order, order_id, info=info)
