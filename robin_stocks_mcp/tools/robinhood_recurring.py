"""Robinhood recurring-investment tools.

These wrap the SDK's recurring-investment helpers, which hit the
undocumented bonfire.robinhood.com/recurring_schedules/ endpoint.
The opt-in rate-limiter toggles (paired with the same upstream PR)
are also exposed here.
"""

from __future__ import annotations

from typing import Any

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread

# ---------------------------------------------------------------------------
# Rate-limiter toggles (local SDK state, not server-side writes)
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_enable_rate_limiting(delay: float = 1.0) -> str:
    """Enable in-process rate limiting for all Robinhood SDK requests.

    `delay` is the minimum seconds between requests. Off by default.
    """
    await to_thread(rh.enable_rate_limiting, delay=delay)
    return f"ok: rate limiting enabled (delay={delay}s)"


@mcp.tool()
@safe_tool()
async def rh_disable_rate_limiting() -> str:
    """Disable in-process rate limiting for Robinhood SDK requests."""
    await to_thread(rh.disable_rate_limiting)
    return "ok: rate limiting disabled"


@mcp.tool()
@safe_tool()
async def rh_get_recurring_investments(
    info: str | None = None,
    account_number: str | None = None,
    asset_types: list[str] | None = None,
    jsonify: bool = True,
) -> Any:
    """List all recurring-investment schedules for the account."""
    return await to_thread(
        rh.get_recurring_investments,
        info=info,
        account_number=account_number,
        asset_types=asset_types,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool()
async def rh_get_next_investment_date(
    frequency: str = "weekly",
    start_date: str | None = None,
    jsonify: bool = True,
) -> Any:
    """Compute when the next investment for a given frequency/start would run."""
    return await to_thread(
        rh.get_next_investment_date,
        frequency=frequency,
        start_date=start_date,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_create_recurring_investment(
    symbol: str,
    amount: float,
    frequency: str = "weekly",
    start_date: str | None = None,
    account_number: str | None = None,
    source_of_funds: str = "buying_power",
    jsonify: bool = True,
) -> Any:
    """Create a recurring-investment schedule for `symbol` at `amount` USD per period.

    `frequency` is one of 'daily', 'weekly', 'biweekly', 'monthly'.
    """
    return await to_thread(
        rh.create_recurring_investment,
        symbol,
        amount,
        frequency=frequency,
        start_date=start_date,
        account_number=account_number,
        source_of_funds=source_of_funds,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_update_recurring_investment(
    schedule_id: str,
    account_number: str | None = None,
    amount: float | None = None,
    frequency: str | None = None,
    state: str | None = None,
    start_date: str | None = None,
    jsonify: bool = True,
) -> Any:
    """Modify an existing recurring-investment schedule (any subset of fields)."""
    return await to_thread(
        rh.update_recurring_investment,
        schedule_id,
        account_number=account_number,
        amount=amount,
        frequency=frequency,
        state=state,
        start_date=start_date,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_cancel_recurring_investment(schedule_id: str, jsonify: bool = True) -> Any:
    """Cancel (state='deleted') a recurring-investment schedule by id."""
    return await to_thread(rh.cancel_recurring_investment, schedule_id, jsonify=jsonify)
